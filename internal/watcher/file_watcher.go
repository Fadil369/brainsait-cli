package watcher

import (
	"log"
	"os"
	"path/filepath"

	"github.com/brainsait/cli/internal/context"
	"github.com/fsnotify/fsnotify"
)

type FileWatcher struct {
	watcher    *fsnotify.Watcher
	contextMgr *context.ContextManager
}

func NewFileWatcher(contextMgr *context.ContextManager) (*FileWatcher, error) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return nil, err
	}

	return &FileWatcher{
		watcher:    watcher,
		contextMgr: contextMgr,
	}, nil
}

func (fw *FileWatcher) WatchProject(projectPath string) error {
	go func() {
		for {
			select {
			case event, ok := <-fw.watcher.Events:
				if !ok {
					return
				}
				log.Println("event:", event)
				if event.Op&fsnotify.Write == fsnotify.Write {
					log.Println("modified file:", event.Name)
					fw.contextMgr.AnalyzeProject(projectPath) // Re-analyze project on change
				}
			case err, ok := <-fw.watcher.Errors:
				if !ok {
					return
				}
				log.Println("error:", err)
			}
		}
	}()

	return filepath.Walk(projectPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return fw.watcher.Add(path)
		}
		return nil
	})
}

func isRelevantFile(path string) bool {
	// Placeholder for relevance logic
	return true
}
