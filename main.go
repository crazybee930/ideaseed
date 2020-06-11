package main

import (
	"os"
	"fmt"
	"log"
	
	"github.com/urfave/cli/v2"
)

func main() {
	app := &cli.App{
		Name: "ideasprout",
		Usage: "Swiftly catch that idea and get back to what you were doing",
		Action: func(c *cli.Context) error {
			fmt.Println("An error occured :/")
			fmt.Println(c)
			return nil
		},
	}
	
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
