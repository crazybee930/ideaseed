package main

import (
	"context"
	"errors"
	"os"

	"github.com/shurcooL/githubv4"
	"golang.org/x/oauth2"
)

// CreateGithubClient creates a githubv4 client to use the GitHub API.
// It logs you in with oauth2, using the GitHub token defined in ./.env
func CreateGithubClient() (*githubv4.Client, error) {
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		return nil, errors.New("token not set; please set the GITHUB_TOKEN environment variable")
	}
	src := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	httpClient := oauth2.NewClient(context.Background(), src)

	client := githubv4.NewClient(httpClient)

	return client, nil
}

// GetGithubUsername returns the GitHub username we are currently logged in with.
func GetGithubUsername(client *githubv4.Client) (string, error) {
	var query struct {
		Viewer struct {
			Login string
		}
	}
	err := client.Query(context.Background(), &query, nil)
	if err != nil {
		return "", err
	}
	return query.Viewer.Login, nil
}

// RepoExists returns a boolean to check if a given repository "owner/name" exists.
func RepoExists(client *githubv4.Client, owner string, name string) bool {
	variables := map[string]interface{}{
		"owner": githubv4.String(owner),
		"name":  githubv4.String(name),
	}
	var query struct {
		Repository struct {
			Description string
		} `graphql:"repository(owner: $owner, name: $name)"`
	}
	err := client.Query(context.Background(), &query, variables)
	return err == nil
}

// CreateCard creates a new project card with text text on repo repoOwner/repoName, in the column #columnNumber of the project #projectNumber
func CreateCard(client *githubv4.Client, repoOwner string, repoName string, projectNumber int, columnNumber int, text string) (string, error) {
	variables := map[string]interface{}{
		"owner":   githubv4.String(repoOwner),
		"name":    githubv4.String(repoName),
	}
	// Get the project id and the column id
	var query struct {
		Repository struct {
			Projects struct {
				nodes struct {
					Name    string
					ID      string
					Number  uint32
					columns struct {
						nodes struct {
							ID   string
							Name string
						}
					} `graphql:"columns(first: 100)"`
				}
			} `graphql:"projects(first: 100)"`
		} `graphql:"repository(owner: $owner, name: $name)"`
	}
	err := client.Query(context.Background(), &query, variables)
	if err != nil {
		return "", err
	}
	for _, repoName := range query.Repository.Projects.nodes.Name {
		println(repoName)
	}
	return "https://ewen.works ( ͡° ͜ʖ ͡°)", nil
}
