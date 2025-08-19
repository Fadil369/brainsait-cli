package plugins

import "fmt"

type PluginManager struct {
	plugins map[string]Plugin
}

func NewPluginManager() *PluginManager {
	return &PluginManager{
		plugins: make(map[string]Plugin),
	}
}

func (pm *PluginManager) RegisterPlugin(plugin Plugin) {
	pm.plugins[plugin.Name()] = plugin
	fmt.Printf("Plugin '%s' registered\n", plugin.Name())
}
