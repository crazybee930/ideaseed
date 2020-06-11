package main

import (
	"fmt"
	"log"
	"os"

	"github.com/urfave/cli/v2"
)

func main() {
	app := &cli.App{
		Name:  "ideasprout",
		Usage: "Swiftly catch that idea and get back to what you were doing",
		Action: func(c *cli.Context) error {
			fmt.Println("-- Work in progress :) --")
			return nil
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
