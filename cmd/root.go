package cmd

import (
    "github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
    Use:   "brainsait",
    Short: "BrainSAIT AI Code Assistant",
    Long:  `Intelligent CLI tool for automated coding with AI`,
}

var (
    cfgFile string
    debug   bool
    model   string = "claude-sonnet-4"
)

func init() {
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file")
    rootCmd.PersistentFlags().BoolVar(&debug, "debug", false, "debug mode")
    rootCmd.PersistentFlags().StringVar(&model, "model", "claude-sonnet-4", "AI model")
    
    // Add subcommands
    rootCmd.AddCommand(chatCmd)
    rootCmd.AddCommand(codeCmd) 
    rootCmd.AddCommand(reviewCmd)
    rootCmd.AddCommand(deployCmd)
}

func Execute() error {
    return rootCmd.Execute()
}
