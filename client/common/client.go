package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	bet    Bet
}

type Bet struct {
	AgencyId string
	Name     string
	Surname  string
	Dni      string
	Dob      string
	BetNum   string
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, bet Bet) *Client {
	client := &Client{
		config: config,
		bet:    bet,
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Info("action: signal_SIGTERM_received | result: in_progress")
		if client.conn != nil {
			_ = client.conn.Close()
		}
	}()

	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	c.createClientSocket()

	message := fmt.Sprintf(
		"%s,%s,%s,%s,%s,%s\n",
		c.bet.AgencyId,
		c.bet.Name,
		c.bet.Surname,
		c.bet.Dni,
		c.bet.Dob,
		c.bet.BetNum,
	)

	if err := c.sendMessage(c.conn, message); err != nil {
		log.Errorf("action: bet_sent | result: fail | error: %v", err)
		c.conn.Close()
		return
	}

	reader := bufio.NewReader(c.conn)
	_, err := reader.ReadString('\n')

	c.conn.Close()
	if err == nil {
		log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s", c.bet.Dni, c.bet.BetNum)
	}
}

func (c *Client) sendMessage(conn net.Conn, msg string) error {
	data := []byte(msg)
	total := 0
	for total < len(data) {
		n, err := conn.Write(data[total:])
		if err != nil {
			return err
		}
		total += n
	}
	return nil
}
