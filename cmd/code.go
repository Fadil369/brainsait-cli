package cmd

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/brainsait/cli/internal/ai"
	ctx "github.com/brainsait/cli/internal/context"
	"github.com/spf13/cobra"
)

var codeCmd = &cobra.Command{
	Use:   "code [prompt]",
	Short: "Generate code",
	Long:  `Generate code based on a prompt`,
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		prompt := strings.Join(args, " ")

		aiClient := ai.NewClaudeClient(os.Getenv("ANTHROPIC_API_KEY"))
		contextMgr := ctx.NewContextManager()

		if workingDir, err := os.Getwd(); err == nil {
			if isGitRepo(workingDir) {
				fmt.Printf("📁 Analyzing project: %s\n", workingDir)
				contextMgr.AnalyzeProject(workingDir)
			}
		}

		projectContext := contextMgr.GetRelevantContext(prompt, 2000)

		response, err := aiClient.GenerateCode(context.Background(), prompt, projectContext)
		if err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			return
		}

		if len(response.Content) > 0 {
			fmt.Println(response.Content[0].Text)
		} else {
			fmt.Println("No code generated.")
		}
	},
}
