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
	-p 	--project=PROJECT-NAME|INDEX  Select which project to put the project too. Can only be used with --gh. [default: 1]
	-c 	--column=COLUMN NAME          Select which column of the project to use. Can only be used with --gh. [default: To-Do]
		--create-columns              Prompt to create non-existant columns specified with --columns.
	-d 	--color=COLOR                 Chooses which color to use for Google Keep cards. Cannot be used with --gh. COLOR can be one of: bl[ue], br[own], d[arkblue], gra[y], gre[en], o[range], pi[nk], pu[rple], r[ed], t[eal], w[hite], y[ellow],
	-t 	--tag=TAG NAME                Adds tags to the Google Keep card. Cannot be used with --gh.
		--create-tags                 Prompt to create non-existant tags specified with --tag.
	-? 	--prompt-mode                 Prompts you for the above options when they are not provided.
	-o	--open                        Open the created card in your browser

Examples: (In all examples, USERNAME refers to your username.)
	# Create a new card with content "Choose audio normalization loudness with --loudness" in USERNAME/phelng > project #1 > column "To-Do" 
	ideaseed --gh -r phelng Choose audio normalization loudness with --loudness
	
	# Create a new yellow card tagged "project", "vfx" in Google Keep with text "Lyrics video for Mazde - Neverland"
	ideaseed -t project -t vfx -d yel Lyrics video for Mazde - Neverland
`

	opts, _ := docopt.ParseDoc(usage)
	// Get the full text
	idea, _ := opts.String("IDEA...")
	
	usingGithub, _ := opts.Bool("--gh")
	if usingGithub {
		gh, err := CreateGithubClient()
		if err != nil {
			println(err.Error())
			return
		}
		repository, usingUserProject := opts.String("--repo")
		if usingUserProject != nil {

		} else {
			repositorySplitted := strings.Split(repository, "/")
			var repoOwner string
			var repoName string
			if len(repositorySplitted) == 1 {
				// We only provided the repo name
				repoOwner, err = GetGithubUsername(gh)
				if err != nil {
					println(err.Error())
					return
				}
				repoName = repositorySplitted[0]
			} else if len(repositorySplitted) == 2 {
				// We also specified the owner
				repoOwner = repositorySplitted[0]
				repoName = repositorySplitted[1]
			}
			// Get the repo
			if !RepoExists(gh, repoOwner, repoName) {
				println("repository " + repoOwner + "/" + repoName + " does not exist")
				return
			}
			// Create the card
			projectNumber, _ := opts.Int("--project")
			columnNumber, _  := opts.Int("--column")
			url, err := CreateCard(gh, repoOwner, repoName, projectNumber, columnNumber, idea)
			if err != nil {
				println(err.Error())
				return
			}
			println(url)
			if flagIsSet, _ := opts.Bool("--open"); flagIsSet {
				openInBrowser(url)
			}
		}
	} else {
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
		if flagIsSet, _ := opts.Bool("--open"); flagIsSet {
			err := openInBrowser("https://keep.google.com/")
			if err != nil {
				println(err.Error())
			}
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
	colorMap := map[string]func(string) string{
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

func openInBrowser(url string) error {
	var err error

	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", url).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	case "darwin":
		err = exec.Command("open", url).Start()
	default:
		return errors.New("Unsupported platform '" + runtime.GOOS + "'")
	}
	return err

}
