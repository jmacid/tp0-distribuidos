package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
}

type Client struct {
	config ClientConfig
	conn   net.Conn
	bets   []Bet
}

type Bet struct {
	AgencyId string
	Name     string
	Surname  string
	Dni      string
	Dob      string
	BetNum   string
}

func NewClient(config ClientConfig, bets []Bet) *Client {
	client := &Client{
		config: config,
		bets:   bets,
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

func (c *Client) StartClientLoop() {
	totalBets := len(c.bets)
	batchSize := c.config.BatchMaxAmount
	if batchSize <= 0 {
		batchSize = 100
	}

	for i := 0; i < totalBets; i += batchSize {
		end := i + batchSize
		if end > totalBets {
			end = totalBets
		}

		batch := c.bets[i:end]
		if err := c.sendBatch(batch); err != nil {
			log.Errorf("action: send_batch | result: fail | error: %v", err)
		}
	}

	if err := c.ConsultarGanadores(); err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | error: %v", err)
	}
}

func (c *Client) sendBatch(batch []Bet) error {
	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.conn.Close()

	for _, bet := range batch {
		msg := createBetMessage(bet)
		if err := c.sendMessage(c.conn, msg); err != nil {
			return err
		}
	}

	if err := c.sendMessage(c.conn, "END_BATCH\n"); err != nil {
		return err
	}

	reader := bufio.NewReader(c.conn)
	response, err := reader.ReadString('\n')
	if err != nil {
		return fmt.Errorf("error leyendo respuesta: %v", err)
	}

	if response != "ACK\n" {
		return fmt.Errorf("no se recibió ACK del servidor")
	}

	log.Infof("action: batch_sent | result: success | cantidad: %d", len(batch))
	return nil
}

func (c *Client) ConsultarGanadores() error {
	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.conn.Close()

	msg := fmt.Sprintf("FIN_AGENCIA,%s\n", c.config.ID)
	if err := c.sendMessage(c.conn, msg); err != nil {
		return err
	}

	reader := bufio.NewReader(c.conn)
	response, err := reader.ReadString('\n')
	if err != nil {
		return fmt.Errorf("error leyendo respuesta ganadores: %v", err)
	}

	response = strings.TrimSpace(response)
	var cant int
	if response == "" {
		cant = 0
	} else {
		ganadores := strings.Split(response, ",")
		cant = len(ganadores)
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", cant)
	return nil
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

func createBetMessage(bet Bet) string {
	return fmt.Sprintf(
		"%s,%s,%s,%s,%s,%s\n",
		bet.AgencyId,
		bet.Name,
		bet.Surname,
		bet.Dni,
		bet.Dob,
		bet.BetNum,
	)
}
