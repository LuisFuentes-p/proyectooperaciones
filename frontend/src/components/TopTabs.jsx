export function TopTabs({ tabs, activeTab, onSelect }) {
  return (
    <nav className="tab-strip" aria-label="Areas disponibles">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`tab-button${activeTab === tab.id ? ' is-active' : ''}${tab.enabled ? '' : ' is-disabled'}`}
          onClick={() => onSelect(tab.id)}
          disabled={!tab.enabled}
          aria-pressed={activeTab === tab.id}
        >
          <span className="tab-label">{tab.label}</span>
          <span className="tab-description">{tab.description}</span>
        </button>
      ))}
    </nav>
  );
}
