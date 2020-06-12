package main

import (
	"errors"
	"fmt"
	"strings"

	"github.com/docopt/docopt-go"
	"github.com/mgutz/ansi"
)

func main() {
	usage := `Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

Usage:
	ideaseed [options] IDEA...

Options:
	-r 	--repo=[OWNER/]REPO           Select which repo to put the idea to. If OWNER/ is omitted, OWNER is your GitHub username
	-g	--gh                          Put the idea to github. If --repo is not given, the card is added to one of the user's projects.
	-p 	--project=PROJECT-NAME        Select which project to put the project too. Can only be used with --gh.
	-c 	--column=COLUMN NAME|INDEX    Select which column of the project to use. Can only be used with --gh.
		--create-columns              Prompt to create non-existant columns specified with --columns.
	-d 	--color=COLOR                 Chooses which color to use for Google Keep cards. Cannot be used with --gh. COLOR can be one of: bl[ue], br[own], d[arkblue], gra[y], gre[en], o[range], pi[nk], pu[rple], r[ed], t[eal], w[hite], y[ellow],
	-t 	--tag=TAG NAME                Adds tags to the Google Keep card. Cannot be used with --gh.
		--create-tags                 Prompt to create non-existant tags specified with --tag.
	-? 	--prompt-mode                 Prompts you for the above options when they are not provided.
`	

	opts, _ := docopt.ParseDoc(usage)
	// Get the color option
	color, _ := opts.String("--color")
	// If we have specified it
	if color != "" {
		// Try to get the full color name (to handle eg. dar => darkblue)
		var err error
		color, err = expandColorName(color)
		// Show the error
		if err != nil {
			fmt.Println(err)
			// If we successfully expanded it, print it (for now!)
		} else {
			println(coloredColorName(color))
		}
	}

}

func expandColorName(color string) (string, error) {
	// All possible color names
	colorNames := []string{
		"blue",
		"brown",
		"darkblue",
		"gray",
		"green",
		"orange",
		"pink",
		"purple",
		"red",
		"teal",
		"white",
		"yellow",
	}
	// Initialize the array of matches
	matchingColorNames := []string{}
	// Filter `colorNames` to only get the color names that start with `color`
	for _, colorName := range colorNames {
		if strings.HasPrefix(colorName, color) {
			matchingColorNames = append(matchingColorNames, colorName)
		}
	}
	// If we have exactly _one_ element of `colorNames` that matches, we return the only
	// element: it's a match!
	if len(matchingColorNames) == 1 {
		return matchingColorNames[0], nil
	}
	// If we had multiple choice, the given color was ambiguous.
	if len(matchingColorNames) > 1 {
		var matchingColorNamesDisplay []string
		for _, matchingColorName := range matchingColorNames {
			matchingColorNamesDisplay = append(matchingColorNamesDisplay, coloredColorName(matchingColorName))
		}
		return "", errors.New("Ambiguous color shorthand '" + color + "': could be one of: " + strings.Join(matchingColorNamesDisplay, ", "))
	}
	// If we had an empty array, then the given color name was incorrect.
	return "", errors.New("Unvalid color '" + color + "'")
}

func coloredColorName(color string) string {
	colorMap := map[string]func(string)string{
		"blue":     ansi.ColorFunc("blue+h"),
		"brown":    ansi.ColorFunc("red"),
		"darkblue": ansi.ColorFunc("blue"),
		"gray":     ansi.ColorFunc("black+h"),
		"green":    ansi.ColorFunc("green"),
		"orange":   ansi.ColorFunc("yellow"),
		"pink":     ansi.ColorFunc("magenta+h"),
		"purple":   ansi.ColorFunc("magenta"),
		"red":      ansi.ColorFunc("red+h"),
		"teal":     ansi.ColorFunc("cyan"),
		"white":    ansi.ColorFunc("off"),
		"yellow":   ansi.ColorFunc("yellow+h"),
	}
	return colorMap[color](color)
}