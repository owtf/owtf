package cli

import (
	"fmt"
	"io"
	"runtime/debug"
	"sort"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/owtf/owtf/internal/model"
)

const banner = `         _____ _ _ _ _____ _____
        |     | | | |_   _|   __|
        |  |  | | | | | | |   __|
        |_____|_____| |_| |__|`

type presentation struct {
	out       io.Writer
	logo      lipgloss.Style
	heading   lipgloss.Style
	label     lipgloss.Style
	code      lipgloss.Style
	detail    lipgloss.Style
	warning   lipgloss.Style
	separator lipgloss.Style
}

func newPresentation(out io.Writer) presentation {
	renderer := lipgloss.NewRenderer(out)
	return presentation{
		out:       out,
		logo:      renderer.NewStyle().Bold(true).Foreground(lipgloss.Color("10")),
		heading:   renderer.NewStyle().Bold(true).Foreground(lipgloss.Color("12")),
		label:     renderer.NewStyle().Bold(true),
		code:      renderer.NewStyle().Foreground(lipgloss.Color("12")),
		detail:    renderer.NewStyle().Foreground(lipgloss.Color("8")),
		warning:   renderer.NewStyle().Bold(true).Foreground(lipgloss.Color("11")),
		separator: renderer.NewStyle().Foreground(lipgloss.Color("8")),
	}
}

// WriteBanner prints the OWTF identity used by interactive commands and startup.
func WriteBanner(out io.Writer) {
	newPresentation(out).writeBanner()
}

func (p presentation) writeBanner() {
	version := "development"
	if info, ok := debug.ReadBuildInfo(); ok && info.Main.Version != "" && info.Main.Version != "(devel)" {
		version = strings.TrimPrefix(info.Main.Version, "v")
	}
	fmt.Fprintln(p.out)
	for _, line := range strings.Split(banner, "\n") {
		fmt.Fprintln(p.out, p.logo.Render(line))
	}
	fmt.Fprintln(p.out)
	fmt.Fprintln(p.out, p.logo.Render("            @owtfp"))
	fmt.Fprintln(p.out, p.logo.Render("        https://owtf.org"))
	fmt.Fprintln(p.out, p.detail.Render("        Version: "+version))
	fmt.Fprintln(p.out)
}

func (p presentation) writePlugins(plugins []model.Plugin) {
	p.writeBanner()
	if len(plugins) == 0 {
		fmt.Fprintln(p.out, p.warning.Render("No plugins found."))
		return
	}

	fmt.Fprintln(p.out, p.heading.Render("Short Intro"))
	fmt.Fprintln(p.out, p.separator.Render("==========="))
	fmt.Fprintln(p.out, "OWTF plugins are organized by assessment surface and execution type.")
	fmt.Fprintln(p.out)
	fmt.Fprintln(p.out, p.label.Render("Plugin Groups"))
	for _, group := range orderedValues(pluginGroups(plugins), groupOrder) {
		fmt.Fprintf(p.out, "  %-10s %s\n", groupLabel(group)+":", groupDescription(group))
	}
	fmt.Fprintln(p.out)
	fmt.Fprintln(p.out, p.label.Render("Plugin Types"))
	for _, pluginType := range orderedValues(pluginTypes(plugins), typeOrder) {
		fmt.Fprintf(p.out, "  %-14s %s\n", typeLabel(pluginType)+":", typeDescription(pluginType))
	}

	grouped := make(map[string]map[string][]model.Plugin)
	for _, item := range plugins {
		if grouped[item.Group] == nil {
			grouped[item.Group] = make(map[string][]model.Plugin)
		}
		grouped[item.Group][item.Type] = append(grouped[item.Group][item.Type], item)
	}
	for _, group := range orderedKeys(grouped, groupOrder) {
		fmt.Fprintln(p.out)
		title := groupLabel(group) + " Plugin List"
		fmt.Fprintln(p.out, p.heading.Render(title))
		fmt.Fprintln(p.out, p.separator.Render(strings.Repeat("=", len(title))))
		for _, pluginType := range orderedKeys(grouped[group], typeOrder) {
			items := grouped[group][pluginType]
			sort.Slice(items, func(i, j int) bool {
				if items[i].ID == items[j].ID {
					return items[i].Title < items[j].Title
				}
				return items[i].ID < items[j].ID
			})
			p.writePluginSection(pluginType, items)
		}
	}
}

func (p presentation) writePluginSection(pluginType string, plugins []model.Plugin) {
	fmt.Fprintln(p.out)
	title := typeLabel(pluginType) + " Plugins"
	fmt.Fprintln(p.out, p.label.Render(title))
	fmt.Fprintln(p.out, p.separator.Render(strings.Repeat("-", len(title))))

	nameWidth, codeWidth := 0, 0
	for _, item := range plugins {
		nameWidth = max(nameWidth, len(pluginName(item)))
		codeWidth = max(codeWidth, len(item.ID))
	}
	for _, item := range plugins {
		name := fmt.Sprintf("%-*s", nameWidth, pluginName(item))
		code := fmt.Sprintf("(%-*s)", codeWidth, item.ID)
		description := item.Description
		if description == "" {
			description = "No description."
		}
		fmt.Fprintf(p.out, "  %s  %s  %s", p.label.Render(name), p.code.Render(code), p.detail.Render(description))
		if item.Availability != "" && item.Availability != "ready" {
			fmt.Fprintf(p.out, "  %s", p.warning.Render("["+item.Availability+"]"))
			if item.Reason != "" {
				fmt.Fprintf(p.out, " %s", p.detail.Render(item.Reason))
			}
		}
		fmt.Fprintln(p.out)
	}
}

func pluginName(item model.Plugin) string {
	return item.Type + ":" + strings.NewReplacer(" ", "_", "/", "_").Replace(item.Title)
}

var groupOrder = []string{"web", "network", "auxiliary", "community"}
var typeOrder = []string{"active", "external", "grep", "semi_passive", "passive", "bruteforce", "dos", "exploit", "selenium", "smb"}

func groupLabel(group string) string {
	switch group {
	case "web":
		return "Web"
	case "network":
		return "Network"
	case "auxiliary":
		return "Auxiliary"
	case "community":
		return "Community"
	default:
		return strings.ReplaceAll(group, "_", " ")
	}
}

func groupDescription(group string) string {
	switch group {
	case "web":
		return "Web application assessment techniques for HTTP and HTTPS targets."
	case "network":
		return "Network discovery, service enumeration, and protocol assessment techniques."
	case "auxiliary":
		return "Supporting assessment tasks that are not specific to one surface."
	case "community":
		return "Community-maintained assessment techniques."
	default:
		return "OWTF assessment techniques."
	}
}

func typeLabel(pluginType string) string {
	switch pluginType {
	case "semi_passive":
		return "Semi-Passive"
	case "bruteforce":
		return "Brute Force"
	case "dos":
		return "DoS"
	case "smb":
		return "SMB"
	default:
		if pluginType == "" {
			return "Unknown"
		}
		return strings.ToUpper(pluginType[:1]) + strings.ReplaceAll(pluginType[1:], "_", " ")
	}
}

func typeDescription(pluginType string) string {
	switch pluginType {
	case "passive":
		return "Reviews public information without sending requests to the target."
	case "semi_passive":
		return "Uses normal requests that should not alter the target."
	case "active":
		return "Sends direct security probes and requires explicit authorization."
	case "grep":
		return "Analyzes HTTP transactions already captured by OWTF."
	case "external":
		return "Provides maintained manual-testing guidance and references."
	case "bruteforce":
		return "Exercises authentication or enumeration techniques deliberately."
	case "dos":
		return "Exercises denial-of-service techniques deliberately."
	default:
		return "Runs an OWTF plugin technique."
	}
}

func pluginGroups(plugins []model.Plugin) map[string]struct{} {
	values := make(map[string]struct{})
	for _, item := range plugins {
		values[item.Group] = struct{}{}
	}
	return values
}

func pluginTypes(plugins []model.Plugin) map[string]struct{} {
	values := make(map[string]struct{})
	for _, item := range plugins {
		values[item.Type] = struct{}{}
	}
	return values
}

func orderedValues(values map[string]struct{}, preferred []string) []string {
	items := make(map[string]struct{}, len(values))
	for value := range values {
		items[value] = struct{}{}
	}
	return orderedKeys(items, preferred)
}

func orderedKeys[T any](values map[string]T, preferred []string) []string {
	keys := make([]string, 0, len(values))
	seen := make(map[string]bool, len(values))
	for _, value := range preferred {
		if _, ok := values[value]; ok {
			keys = append(keys, value)
			seen[value] = true
		}
	}
	var remaining []string
	for value := range values {
		if !seen[value] {
			remaining = append(remaining, value)
		}
	}
	sort.Strings(remaining)
	return append(keys, remaining...)
}
