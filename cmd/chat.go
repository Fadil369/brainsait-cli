package cmd

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"regexp"
	"strings"

	"github.com/brainsait/cli/internal/ai"
	ctx "github.com/brainsait/cli/internal/context"
	"github.com/brainsait/cli/internal/executor"
	"github.com/brainsait/cli/internal/watcher"
	"github.com/spf13/cobra"
)

var chatCmd = &cobra.Command{
	Use:   "chat",
	Short: "Start interactive chat session",
	Long:  `Start an interactive coding session with BrainSAIT AI`,
	Run:   runChatSession,
}

func runChatSession(cmd *cobra.Command, args []string) {
	fmt.Println("🧠 BrainSAIT Code Assistant")
	fmt.Println("Type 'exit' to quit, 'clear' to clear context")
	fmt.Println("----------------------------------------")

	var aiClient ai.AIClient
	switch {
	case strings.HasPrefix(model, "claude"):
		aiClient = ai.NewClaudeClient(os.Getenv("ANTHROPIC_API_KEY"))
	case strings.HasPrefix(model, "gpt"):
		aiClient = ai.NewOpenAIClient(os.Getenv("OPENAI_API_KEY"))
	default:
		fmt.Printf("❌ Unknown model: %s\n", model)
		return
	}

	contextMgr := ctx.NewContextManager()

	if workingDir, err := os.Getwd(); err == nil {
		if isGitRepo(workingDir) {
			fmt.Printf("📁 Analyzing project: %s\n", workingDir)
			contextMgr.AnalyzeProject(workingDir)

			fileWatcher, err := watcher.NewFileWatcher(contextMgr)
			if err != nil {
				log.Fatalf("Failed to create file watcher: %v", err)
			}
			fileWatcher.WatchProject(workingDir)
		}
	}

	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("\n🤖 > ")

		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())

		switch input {
		case "exit", "quit":
			fmt.Println("👋 Goodbye!")
			return
		case "clear":
			contextMgr.ClearSession()
			fmt.Println("🧹 Context cleared")
			continue
		case "context":
			fmt.Println(contextMgr.GetContextSummary())
			continue
		}

		if input == "" {
			continue
		}

		responseText, err := processUserInput(aiClient, contextMgr, input)
		if err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			continue
		}

		fmt.Printf("\n%s\n", responseText)

		code, lang := extractCode(responseText)
		if code != "" {
			fmt.Printf("\n---\nDetected %s code:\n%s\n---", lang, code)
			fmt.Print("Execute this code? (y/n) ")

			if scanner.Scan() {
				answer := strings.TrimSpace(scanner.Text())
				if strings.ToLower(answer) == "y" {
					executor := executor.NewCodeExecutor(".")
					result, err := executor.ExecuteCode(context.Background(), code, lang)
					if err != nil {
						fmt.Printf("❌ Error: %v\n", err)
						continue
					}
					fmt.Printf("\nExecution Result:\n---\n%s\n---", result.Output)
				}
			}
		}
	}
}

func processUserInput(aiClient ai.AIClient, contextMgr *ctx.ContextManager, input string) (string, error) {
	projectContext := contextMgr.GetRelevantContext(input, 2000)

	response, err := aiClient.GenerateCode(context.Background(), input, projectContext)
	if err != nil {
		return "", err
	}

	var responseText string
	if len(response.Content) > 0 {
		responseText = response.Content[0].Text
	}

	contextMgr.AddToHistory(input, responseText)

	return responseText, nil
}

func extractCode(text string) (string, string) {
	re := regexp.MustCompile("```(?P<lang>\\w+)\n(?P<code>[\\s\\S]*?)\n```")
	matches := re.FindStringSubmatch(text)
	if len(matches) > 2 {
		return matches[2], matches[1]
	}
	return "", ""
}

func isGitRepo(path string) bool {
    if _, err := os.Stat(path + ".git"); err == nil {
        return true
    }
    return false
}
