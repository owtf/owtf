# Proxy Tabs Component

This directory contains the tabbed interface for the OWTF Proxy page, providing an organized and extensible structure for different proxy management features.

## Components

### `ProxyTabs.tsx`
The main tab navigation component that renders the tab buttons and handles tab switching.

### `HistoryTab.tsx`
Displays the proxy history with filters, table, and statistics. This tab contains all the original proxy history functionality.

### `InterceptorsTab.tsx`
Manages proxy interceptors for request/response modification. This tab contains the interceptor management interface.

### `RepeaterTab.tsx`
Provides HTTP request/response replay and modification capabilities for testing and debugging.

## Usage

```tsx
import ProxyTabs, { HistoryTab, InterceptorsTab, RepeaterTab } from '../../components/ProxyTabs';

// Define tabs
const tabs = [
  { id: 'history', label: 'History', icon: '📋' },
  { id: 'interceptors', label: 'Interceptors', icon: '⚙️' },
  { id: 'repeater', label: 'Repeater', icon: '🔄' },
];

// Use in component
<ProxyTabs
  tabs={tabs}
  activeTab={activeTab}
  onTabChange={handleTabChange}
/>

// Render tab content
{activeTab === 'history' && <HistoryTab {...props} />}
{activeTab === 'interceptors' && <InterceptorsTab />}
{activeTab === 'repeater' && <RepeaterTab />}
```

## Adding New Tabs

To add a new tab:

1. Create a new component (e.g., `NewFeatureTab.tsx`)
2. Add it to the `index.ts` exports
3. Add the tab definition to the tabs array
4. Add the case in the `renderTabContent()` function
5. Add any necessary styling

## Structure Benefits

- **Separation of Concerns**: Each feature has its own tab and component
- **Extensibility**: Easy to add new tabs for future features
- **Maintainability**: Clear organization and easy to find specific functionality
- **User Experience**: Clean, organized interface similar to professional tools
- **Responsive Design**: Tabs adapt to different screen sizes

## Current Tabs

- **History**: Proxy request/response history with filtering and statistics
- **Interceptors**: Request/response modification and interception rules
- **Repeater**: HTTP request replay and modification for testing

