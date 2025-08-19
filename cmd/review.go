package cmd

import (
	"context"
	"fmt"
	"io/ioutil"
	"os"

	"github.com/brainsait/cli/internal/ai"
	"github.com/spf13/cobra"
)

var reviewCmd = &cobra.Command{
	Use:   "review [file_path]",
	Short: "Review code",
	Long:  `Review a code file`,
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filePath := args[0]

		content, err := ioutil.ReadFile(filePath)
		if err != nil {
			fmt.Printf("❌ Error reading file: %v\n", err)
			return
		}

		aiClient := ai.NewClaudeClient(os.Getenv("ANTHROPIC_API_KEY"))

		prompt := fmt.Sprintf("Please review the following code:\n\n```\n%s\n```", string(content))

		response, err := aiClient.GenerateCode(context.Background(), prompt, "")
		if err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			return
		}

		if len(response.Content) > 0 {
			fmt.Println(response.Content[0].Text)
		} else {
			fmt.Println("No review generated.")
		}
	},
}
