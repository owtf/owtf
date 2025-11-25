import React from 'react';

export interface ProxyTab {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
}

interface ProxyTabsProps {
  tabs: ProxyTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

const ProxyTabs: React.FC<ProxyTabsProps> = ({ 
  tabs, 
  activeTab, 
  onTabChange, 
  className 
}) => {
  return (
    <div className={`proxy-tabs ${className || ''}`}>
      <div className="proxy-tabs__navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`btn btn-lg proxy-tabs__tab ${activeTab === tab.id ? 'btn-primary proxy-tabs__tab--active' : 'btn-outline-secondary'} ${tab.disabled ? 'proxy-tabs__tab--disabled' : ''}`}
            onClick={() => !tab.disabled && onTabChange(tab.id)}
            disabled={tab.disabled}
            type="button"
          >
            {tab.icon && <span className="proxy-tabs__tab-icon me-2">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ProxyTabs;
