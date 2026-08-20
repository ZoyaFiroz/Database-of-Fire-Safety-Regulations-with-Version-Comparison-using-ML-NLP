const FILTERS = ["all", "modified", "added", "removed", "unchanged"];

export default function FilterBar({ activeFilter, onFilterChange, searchTerm, onSearchChange }) {
  return (
    <div className="filter-bar">
      <div className="filter-tabs">
        {FILTERS.map((f) => (
          <button
            key={f}
            className={`tab-btn ${activeFilter === f ? "active" : ""}`}
            onClick={() => onFilterChange(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>
      <input
        type="text"
        className="search-box"
        placeholder="Search clause (e.g. 11.5, 7.4)..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
      />
    </div>
  );
}
