package main

import (
	"fmt"

	"github.com/docopt/docopt-go"
)

func main() {
	usage := `Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

Usage:
	ideasprout [options] IDEA...

Options:
	-g 	--gh=[[OWNER/]REPO]     	  Put the idea to github. If no argument is given, the card is added to one of the user's projects.
	-p 	--project=PROJECT-NAME  	  Select which project to put the project too. Can only be used with --gh.
	-c 	--column=COLUMN NAME|INDEX    Select which column of the project to use. Can only be used with --gh.
		--create-columns        	  Prompt to create non-existant columns specified with --columns.
	-d 	--color=COLOR           	  Chooses which color to use for Google Keep cards. Cannot be used with --gh. COLOR can be one of: bl[ue], br[own], d[arkblue], gra[y], gre[en], o[range], pi[nk], pu[rple], r[ed], t[eal], w[hite], y[ellow],
	-t 	--tag=TAG NAME          	  Adds tags to the Google Keep card. Cannot be used with --gh.
		--create-tags           	  Prompt to create non-existant tags specified with --tag.
	-? 	--prompt-mode           	  Prompts you for the above options when they are not provided.
`

	opts, _ := docopt.ParseDoc(usage)
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
