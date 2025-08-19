package context

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type ProjectContext struct {
	ID           string            `json:"id"`
	Path         string            `json:"path"`
	Language     string            `json:"language"`
	Framework    string            `json:"framework"`
	Files        []FileInfo        `json:"files"`
	Dependencies map[string]string `json:"dependencies"`
	LastUpdated  time.Time         `json:"last_updated"`
}

type FileInfo struct {
	Path         string    `json:"path"`
	Size         int64     `json:"size"`
	Modified     time.Time `json:"modified"`
	Language     string    `json:"language"`
	Importance   int       `json:"importance"` // 1-10 relevance score
}

type SessionEntry struct {
	Input    string
	Response string
	Timestamp time.Time
}

type ContextManager struct {
	currentProject *ProjectContext
	sessionHistory []SessionEntry
	maxHistorySize int
}

func NewContextManager() *ContextManager {
	return &ContextManager{
		maxHistorySize: 50,
		sessionHistory: make([]SessionEntry, 0),
	}
}

func (cm *ContextManager) AnalyzeProject(projectPath string) error {
	ctx := &ProjectContext{
		ID:   generateProjectID(projectPath),
		Path: projectPath,
	}

	if err := cm.scanProjectFiles(ctx); err != nil {
		return err
	}

	cm.currentProject = ctx
	return nil
}

func (cm *ContextManager) scanProjectFiles(ctx *ProjectContext) error {
	return filepath.Walk(ctx.Path, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			if info.Name() == ".git" || info.Name() == "node_modules" {
				return filepath.SkipDir
			}
			return nil
		}

		file := FileInfo{
			Path:     path,
			Size:     info.Size(),
			Modified: info.ModTime(),
			Language: getLanguageFromExtension(path),
		}
		ctx.Files = append(ctx.Files, file)

		return nil
	})
}

func getLanguageFromExtension(path string) string {
	ext := strings.ToLower(filepath.Ext(path))
	switch ext {
	case ".go":
		return "Go"
	case ".js":
		return "JavaScript"
	case ".ts":
		return "TypeScript"
	case ".py":
		return "Python"
	case ".java":
		return "Java"
	case ".html":
		return "HTML"
	case ".css":
		return "CSS"
	case ".md":
		return "Markdown"
	default:
		return "Unknown"
	}
}

func generateProjectID(path string) string {
	h := sha1.New()
	h.Write([]byte(path))
	return hex.EncodeToString(h.Sum(nil))
}

func (cm *ContextManager) GetRelevantContext(query string, maxTokens int) string {
	var contextBuilder strings.Builder
	if cm.currentProject != nil {
		contextBuilder.WriteString(fmt.Sprintf("Project Path: %s\n", cm.currentProject.Path))
		contextBuilder.WriteString("Files:\n")
		for _, file := range cm.currentProject.Files {
			if strings.Contains(file.Path, query) { // Simple matching logic
				content, err := os.ReadFile(file.Path)
				if err == nil {
					if contextBuilder.Len()+len(content) > maxTokens {
						break // Stop if context exceeds maxTokens
					}
					contextBuilder.WriteString(fmt.Sprintf("---\n%s---\n%s\n", file.Path, content))
				}
			}
		}
	}
	return contextBuilder.String()
}

func (cm *ContextManager) ClearSession() {
    cm.sessionHistory = make([]SessionEntry, 0)
}

func (cm *ContextManager) GetContextSummary() string {
    if cm.currentProject != nil {
        return "Project: " + cm.currentProject.Path
    }
    return "No project loaded."
}

func (cm *ContextManager) AddToHistory(input, response string) {
    entry := SessionEntry{
        Input:    input,
        Response: response,
        Timestamp: time.Now(),
    }
    cm.sessionHistory = append(cm.sessionHistory, entry)
    if len(cm.sessionHistory) > cm.maxHistorySize {
        cm.sessionHistory = cm.sessionHistory[1:]
    }
}
