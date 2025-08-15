/**
 * ProxyEntryDetail
 *
 * Component to display detailed information about a proxy entry
 */

import React, { useState } from "react";
import { Dialog, Tab, Tablist, Pane, Button, Code } from "evergreen-ui";

interface ProxyEntryDetailProps {
  entry: any;
  onClose: () => void;
}

const ProxyEntryDetail: React.FC<ProxyEntryDetailProps> = ({ entry, onClose }) => {
  const [selectedTab, setSelectedTab] = useState(0);

  const tabs = [
    { index: 0, tab: "Headers" },
    { index: 1, tab: "Body" },
    { index: 2, tab: "Raw" }
  ];

  const formatHeaders = (headers: any) => {
    if (!headers || typeof headers !== "object") return "No headers";
    
    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join("\n");
  };

  const formatBody = (body: any) => {
    if (!body) return "No body content";
    
    if (typeof body === "string") {
      // Try to format as JSON if possible
      try {
        const parsed = JSON.parse(body);
        return JSON.stringify(parsed, null, 2);
      } catch {
        return body;
      }
    }
    
    return String(body);
  };

  const formatRaw = (entry: any) => {
    const lines = [];
    
    // First line
    if (entry.direction === "REQUEST") {
      lines.push(`${entry.method} ${entry.url} HTTP/1.1`);
    } else {
      lines.push(`HTTP/1.1 ${entry.status_code} Response`);
    }
    
    // Headers
    if (entry.headers && typeof entry.headers === "object") {
      Object.entries(entry.headers).forEach(([key, value]) => {
        lines.push(`${key}: ${value}`);
      });
    }
    
    // Empty line
    lines.push("");
    
    // Body
    if (entry.body) {
      lines.push(formatBody(entry.body));
    }
    
    return lines.join("\n");
  };

  return (
    <Dialog
      isShown={true}
      title={`${entry.direction} - ${entry.method} ${entry.url}`}
      onCloseComplete={onClose}
      width="80vw"
      height="80vh"
    >
      <Pane display="flex" flexDirection="column" height="100%">
        <Pane borderBottom="default" padding={16}>
          <Tablist>
            {tabs.map((tab) => (
              <Tab
                key={tab.index}
                isSelected={selectedTab === tab.index}
                onSelect={() => setSelectedTab(tab.index)}
              >
                {tab.tab}
              </Tab>
            ))}
          </Tablist>
        </Pane>

        <Pane flex={1} padding={16} overflow="auto">
          {selectedTab === 0 && (
            <div className="proxyEntryDetail__headers">
              <h4>Headers</h4>
              <Code
                appearance="minimal"
                size={300}
                isBlock
                whiteSpace="pre-wrap"
              >
                {formatHeaders(entry.headers)}
              </Code>
            </div>
          )}

          {selectedTab === 1 && (
            <div className="proxyEntryDetail__body">
              <h4>Body</h4>
              <Code
                appearance="minimal"
                size={300}
                isBlock
                whiteSpace="pre-wrap"
              >
                {formatBody(entry.body)}
              </Code>
            </div>
          )}

          {selectedTab === 2 && (
            <div className="proxyEntryDetail__raw">
              <h4>Raw</h4>
              <Code
                appearance="minimal"
                size={300}
                isBlock
                whiteSpace="pre-wrap"
              >
                {formatRaw(entry)}
              </Code>
            </div>
          )}
        </Pane>

        <Pane borderTop="default" padding={16}>
          <div className="proxyEntryDetail__metadata">
            <div><strong>Timestamp:</strong> {entry.timestamp}</div>
            <div><strong>Protocol:</strong> {entry.protocol}</div>
            <div><strong>Direction:</strong> {entry.direction}</div>
            {entry.body_size && (
              <div><strong>Body Size:</strong> {entry.body_size} bytes</div>
            )}
          </div>
        </Pane>
      </Pane>
    </Dialog>
  );
};

export default ProxyEntryDetail; 