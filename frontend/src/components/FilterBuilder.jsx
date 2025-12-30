import { useState } from 'react'
import { ChevronDown, ChevronRight, RotateCcw } from 'lucide-react'

// Genre lists
const GENRES_MOVIE = [
  { id: 28, name: 'Action' },
  { id: 12, name: 'Adventure' },
  { id: 16, name: 'Animation' },
  { id: 35, name: 'Comedy' },
  { id: 80, name: 'Crime' },
  { id: 99, name: 'Documentary' },
  { id: 18, name: 'Drama' },
  { id: 10751, name: 'Family' },
  { id: 14, name: 'Fantasy' },
  { id: 36, name: 'History' },
  { id: 27, name: 'Horror' },
  { id: 10402, name: 'Music' },
  { id: 9648, name: 'Mystery' },
  { id: 10749, name: 'Romance' },
  { id: 878, name: 'Science Fiction' },
  { id: 10770, name: 'TV Movie' },
  { id: 53, name: 'Thriller' },
  { id: 10752, name: 'War' },
  { id: 37, name: 'Western' },
]

const GENRES_TV = [
  { id: 10759, name: 'Action & Adventure' },
  { id: 16, name: 'Animation' },
  { id: 35, name: 'Comedy' },
  { id: 80, name: 'Crime' },
  { id: 99, name: 'Documentary' },
  { id: 18, name: 'Drama' },
  { id: 10751, name: 'Family' },
  { id: 10762, name: 'Kids' },
  { id: 9648, name: 'Mystery' },
  { id: 10763, name: 'News' },
  { id: 10764, name: 'Reality' },
  { id: 10765, name: 'Sci-Fi & Fantasy' },
  { id: 10766, name: 'Soap' },
  { id: 10767, name: 'Talk' },
  { id: 10768, name: 'War & Politics' },
  { id: 37, name: 'Western' },
]

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'de', label: 'German' },
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
  { value: 'it', label: 'Italian' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'zh', label: 'Chinese' },
  { value: 'hi', label: 'Hindi' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ru', label: 'Russian' },
  { value: 'ar', label: 'Arabic' },
  { value: 'nl', label: 'Dutch' },
  { value: 'pl', label: 'Polish' },
  { value: 'sv', label: 'Swedish' },
  { value: 'da', label: 'Danish' },
  { value: 'no', label: 'Norwegian' },
  { value: 'fi', label: 'Finnish' },
  { value: 'tr', label: 'Turkish' },
  { value: 'th', label: 'Thai' },
]

const COUNTRIES = [
  { value: 'US', label: 'United States' },
  { value: 'GB', label: 'United Kingdom' },
  { value: 'DE', label: 'Germany' },
  { value: 'FR', label: 'France' },
  { value: 'ES', label: 'Spain' },
  { value: 'IT', label: 'Italy' },
  { value: 'JP', label: 'Japan' },
  { value: 'KR', label: 'South Korea' },
  { value: 'CN', label: 'China' },
  { value: 'IN', label: 'India' },
  { value: 'CA', label: 'Canada' },
  { value: 'AU', label: 'Australia' },
  { value: 'BR', label: 'Brazil' },
  { value: 'MX', label: 'Mexico' },
  { value: 'RU', label: 'Russia' },
  { value: 'SE', label: 'Sweden' },
  { value: 'DK', label: 'Denmark' },
  { value: 'NO', label: 'Norway' },
  { value: 'NL', label: 'Netherlands' },
  { value: 'AT', label: 'Austria' },
  { value: 'CH', label: 'Switzerland' },
]

const WATCH_PROVIDERS = [
  { id: 8, name: 'Netflix' },
  { id: 9, name: 'Amazon Prime Video' },
  { id: 337, name: 'Disney+' },
  { id: 2, name: 'Apple TV' },
  { id: 350, name: 'Apple TV+' },
  { id: 531, name: 'Paramount+' },
  { id: 1899, name: 'Max' },
  { id: 387, name: 'Peacock' },
  { id: 15, name: 'Hulu' },
  { id: 283, name: 'Crunchyroll' },
  { id: 384, name: 'HBO Max' },
  { id: 30, name: 'WOW' },
  { id: 421, name: 'Joyn Plus' },
  { id: 298, name: 'RTL+' },
  { id: 354, name: 'MagentaTV' },
]

const CERTIFICATIONS_MOVIE = [
  { value: 'G', label: 'G - General Audiences' },
  { value: 'PG', label: 'PG - Parental Guidance' },
  { value: 'PG-13', label: 'PG-13 - Parents Strongly Cautioned' },
  { value: 'R', label: 'R - Restricted' },
  { value: 'NC-17', label: 'NC-17 - Adults Only' },
]

const CERTIFICATIONS_TV = [
  { value: 'TV-Y', label: 'TV-Y - All Children' },
  { value: 'TV-Y7', label: 'TV-Y7 - Older Children' },
  { value: 'TV-G', label: 'TV-G - General Audience' },
  { value: 'TV-PG', label: 'TV-PG - Parental Guidance' },
  { value: 'TV-14', label: 'TV-14 - Parents Strongly Cautioned' },
  { value: 'TV-MA', label: 'TV-MA - Mature Audience' },
]

const RELEASE_TYPES = [
  { value: 1, label: 'Premiere' },
  { value: 2, label: 'Theatrical (Limited)' },
  { value: 3, label: 'Theatrical' },
  { value: 4, label: 'Digital' },
  { value: 5, label: 'Physical' },
  { value: 6, label: 'TV' },
]

const TV_STATUS = [
  { value: 0, label: 'Returning Series' },
  { value: 1, label: 'Planned' },
  { value: 2, label: 'In Production' },
  { value: 3, label: 'Ended' },
  { value: 4, label: 'Cancelled' },
  { value: 5, label: 'Pilot' },
]

const MONETIZATION_TYPES = [
  { value: 'flatrate', label: 'Streaming (Flatrate)' },
  { value: 'free', label: 'Free' },
  { value: 'ads', label: 'Free with Ads' },
  { value: 'rent', label: 'Rent' },
  { value: 'buy', label: 'Buy' },
]

// Collapsible Section Component
function FilterSection({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="filter-section">
      <button
        className="filter-section-header"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        <span>{title}</span>
      </button>
      {isOpen && (
        <div className="filter-section-content">
          {children}
        </div>
      )}
    </div>
  )
}

// Range Slider Component
function RangeSlider({ label, min, max, step = 1, value, onChange, suffix = '' }) {
  const [minVal, maxVal] = value || [min, max]

  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <div className="range-inputs">
        <input
          type="number"
          className="form-input small"
          value={minVal}
          onChange={(e) => onChange([parseFloat(e.target.value) || min, maxVal])}
          min={min}
          max={max}
          step={step}
        />
        <span className="range-separator">to</span>
        <input
          type="number"
          className="form-input small"
          value={maxVal}
          onChange={(e) => onChange([minVal, parseFloat(e.target.value) || max])}
          min={min}
          max={max}
          step={step}
        />
        {suffix && <span className="range-suffix">{suffix}</span>}
      </div>
    </div>
  )
}

// Multi-Select Chips Component
function MultiSelectChips({ label, options, value = [], onChange, idKey = 'id', labelKey = 'name' }) {
  const toggleOption = (optionValue) => {
    if (value.includes(optionValue)) {
      onChange(value.filter(v => v !== optionValue))
    } else {
      onChange([...value, optionValue])
    }
  }

  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <div className="chip-container">
        {options.map((opt) => (
          <button
            key={opt[idKey]}
            className={`chip ${value.includes(opt[idKey]) ? 'chip-active' : ''}`}
            onClick={() => toggleOption(opt[idKey])}
          >
            {opt[labelKey]}
          </button>
        ))}
      </div>
    </div>
  )
}

// Single Select Component
function SingleSelect({ label, options, value, onChange, placeholder = 'Select...', valueKey = 'value', labelKey = 'label' }) {
  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <select
        className="form-select"
        value={value || ''}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt[valueKey]} value={opt[valueKey]}>{opt[labelKey]}</option>
        ))}
      </select>
    </div>
  )
}

// Multi Select Dropdown Component
function MultiSelectDropdown({ label, options, value = [], onChange, valueKey = 'value', labelKey = 'label', placeholder = 'Select...' }) {
  const [isOpen, setIsOpen] = useState(false)

  const toggleOption = (optionValue) => {
    if (value.includes(optionValue)) {
      onChange(value.filter(v => v !== optionValue))
    } else {
      onChange([...value, optionValue])
    }
  }

  const selectedLabels = value
    .map(v => options.find(opt => opt[valueKey] === v)?.[labelKey])
    .filter(Boolean)

  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <div className="multi-select-dropdown">
        <button
          type="button"
          className="multi-select-trigger"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="multi-select-text">
            {selectedLabels.length > 0
              ? selectedLabels.length <= 2
                ? selectedLabels.join(', ')
                : `${selectedLabels.length} selected`
              : placeholder}
          </span>
          <ChevronDown size={16} className={`multi-select-arrow ${isOpen ? 'open' : ''}`} />
        </button>
        {isOpen && (
          <>
            <div className="multi-select-backdrop" onClick={() => setIsOpen(false)} />
            <div className="multi-select-menu">
              {options.map((opt) => (
                <label key={opt[valueKey]} className="multi-select-option">
                  <input
                    type="checkbox"
                    checked={value.includes(opt[valueKey])}
                    onChange={() => toggleOption(opt[valueKey])}
                  />
                  <span>{opt[labelKey]}</span>
                </label>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// Number Input Component
function NumberInput({ label, value, onChange, min, max, placeholder }) {
  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <input
        type="number"
        className="form-input"
        value={value || ''}
        onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
        min={min}
        max={max}
        placeholder={placeholder}
      />
    </div>
  )
}

// Date Input Component
function DateInput({ label, value, onChange }) {
  return (
    <div className="filter-item">
      <label className="filter-label">{label}</label>
      <input
        type="date"
        className="form-input"
        value={value || ''}
        onChange={(e) => onChange(e.target.value || null)}
      />
    </div>
  )
}

export default function FilterBuilder({ filters, onChange, mediaType = 'movie' }) {
  const genres = mediaType === 'movie' ? GENRES_MOVIE : GENRES_TV
  const certifications = mediaType === 'movie' ? CERTIFICATIONS_MOVIE : CERTIFICATIONS_TV

  // Convert filters array to object for easier manipulation
  const getFilterValue = (field) => {
    const filter = filters.find(f => f.field === field)
    return filter?.value
  }

  const setFilterValue = (field, value, operator = 'eq') => {
    const newFilters = filters.filter(f => f.field !== field)
    if (value !== null && value !== undefined && value !== '' &&
        !(Array.isArray(value) && value.length === 0)) {
      newFilters.push({ field, operator, value })
    }
    onChange(newFilters)
  }

  // Special handling for range filters (creates two filter entries)
  const getRangeValue = (fieldGte, fieldLte, defaultMin, defaultMax) => {
    const gteFilter = filters.find(f => f.field === fieldGte)
    const lteFilter = filters.find(f => f.field === fieldLte)
    const minVal = gteFilter?.value ?? defaultMin
    const maxVal = lteFilter?.value ?? defaultMax
    // Only return if at least one is different from default
    if (minVal !== defaultMin || maxVal !== defaultMax) {
      return [minVal, maxVal]
    }
    return [defaultMin, defaultMax]
  }

  const setRangeValue = (fieldGte, fieldLte, values, defaultMin, defaultMax) => {
    let newFilters = filters.filter(f => f.field !== fieldGte && f.field !== fieldLte)
    const [minVal, maxVal] = values
    if (minVal !== defaultMin) {
      newFilters.push({ field: fieldGte, operator: 'gte', value: minVal })
    }
    if (maxVal !== defaultMax) {
      newFilters.push({ field: fieldLte, operator: 'lte', value: maxVal })
    }
    onChange(newFilters)
  }

  const resetFilters = () => {
    onChange([])
  }

  const activeFilterCount = filters.length

  return (
    <div className="filter-builder">
      <div className="filter-builder-header">
        <h3>Filters {activeFilterCount > 0 && <span className="badge">{activeFilterCount}</span>}</h3>
        {activeFilterCount > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={resetFilters}>
            <RotateCcw size={14} />
            Reset
          </button>
        )}
      </div>

      {/* Ratings & Votes */}
      <FilterSection title="Ratings & Votes" defaultOpen={true}>
        <RangeSlider
          label="TMDB Rating"
          min={0}
          max={10}
          step={0.5}
          value={getRangeValue('vote_average', 'vote_average_lte', 0, 10)}
          onChange={(vals) => setRangeValue('vote_average', 'vote_average_lte', vals, 0, 10)}
        />
        <NumberInput
          label="Minimum Votes"
          value={getFilterValue('vote_count')}
          onChange={(v) => setFilterValue('vote_count', v, 'gte')}
          min={0}
          placeholder="e.g. 100"
        />
      </FilterSection>

      {/* Release & Dates */}
      <FilterSection title="Release & Dates">
        <NumberInput
          label="Year"
          value={getFilterValue('year')}
          onChange={(v) => setFilterValue('year', v)}
          min={1900}
          max={2030}
          placeholder="e.g. 2024"
        />
        <div className="filter-row-2">
          <DateInput
            label="Released After"
            value={getFilterValue('release_date_gte')}
            onChange={(v) => setFilterValue('release_date_gte', v, 'gte')}
          />
          <DateInput
            label="Released Before"
            value={getFilterValue('release_date_lte')}
            onChange={(v) => setFilterValue('release_date_lte', v, 'lte')}
          />
        </div>
        {mediaType === 'movie' && (
          <MultiSelectChips
            label="Release Type"
            options={RELEASE_TYPES}
            value={getFilterValue('with_release_type') || []}
            onChange={(v) => setFilterValue('with_release_type', v, 'in')}
            idKey="value"
            labelKey="label"
          />
        )}
        {mediaType === 'tv' && (
          <MultiSelectChips
            label="Show Status"
            options={TV_STATUS}
            value={getFilterValue('with_status') || []}
            onChange={(v) => setFilterValue('with_status', v, 'in')}
            idKey="value"
            labelKey="label"
          />
        )}
      </FilterSection>

      {/* Genres */}
      <FilterSection title="Genres">
        <MultiSelectChips
          label="Include Genres"
          options={genres}
          value={getFilterValue('with_genres') || []}
          onChange={(v) => setFilterValue('with_genres', v, 'in')}
        />
        <MultiSelectChips
          label="Exclude Genres"
          options={genres}
          value={getFilterValue('without_genres') || []}
          onChange={(v) => setFilterValue('without_genres', v, 'in')}
        />
      </FilterSection>

      {/* Language & Region */}
      <FilterSection title="Language & Region">
        <MultiSelectDropdown
          label="Original Language"
          options={LANGUAGES}
          value={getFilterValue('with_original_language') || []}
          onChange={(v) => setFilterValue('with_original_language', v, 'in')}
          placeholder="Any language"
        />
        <MultiSelectDropdown
          label="Origin Country"
          options={COUNTRIES}
          value={getFilterValue('with_origin_country') || []}
          onChange={(v) => setFilterValue('with_origin_country', v, 'in')}
          placeholder="Any country"
        />
      </FilterSection>

      {/* Streaming */}
      <FilterSection title="Streaming Services">
        <MultiSelectDropdown
          label="Watch Regions (select countries to check availability)"
          options={COUNTRIES}
          value={getFilterValue('watch_region') || []}
          onChange={(v) => setFilterValue('watch_region', v, 'in')}
          placeholder="Select regions..."
        />
        <MultiSelectChips
          label="Streaming Providers"
          options={WATCH_PROVIDERS}
          value={getFilterValue('with_watch_providers') || []}
          onChange={(v) => {
            // Auto-set watch_region if not already set
            const currentRegions = getFilterValue('watch_region') || []
            if (v.length > 0 && currentRegions.length === 0) {
              setFilterValue('watch_region', ['US'], 'in')
            }
            setFilterValue('with_watch_providers', v, 'in')
          }}
        />
        <MultiSelectChips
          label="Availability Type"
          options={MONETIZATION_TYPES}
          value={getFilterValue('with_watch_monetization_types') || []}
          onChange={(v) => setFilterValue('with_watch_monetization_types', v, 'in')}
          idKey="value"
          labelKey="label"
        />
      </FilterSection>

      {/* Runtime & Certification */}
      <FilterSection title="Runtime & Certification">
        <RangeSlider
          label="Runtime"
          min={0}
          max={300}
          step={5}
          value={getRangeValue('with_runtime', 'with_runtime_lte', 0, 300)}
          onChange={(vals) => setRangeValue('with_runtime', 'with_runtime_lte', vals, 0, 300)}
          suffix="min"
        />
        <SingleSelect
          label="Certification"
          options={certifications}
          value={getFilterValue('certification')}
          onChange={(v) => setFilterValue('certification', v)}
          placeholder="Any rating"
        />
      </FilterSection>

      {/* Advanced */}
      <FilterSection title="Advanced">
        <NumberInput
          label="Cast (Person ID)"
          value={getFilterValue('with_cast')}
          onChange={(v) => setFilterValue('with_cast', v)}
          placeholder="TMDB Person ID"
        />
        <NumberInput
          label="Crew (Person ID)"
          value={getFilterValue('with_crew')}
          onChange={(v) => setFilterValue('with_crew', v)}
          placeholder="TMDB Person ID"
        />
        <NumberInput
          label="Production Company (ID)"
          value={getFilterValue('with_companies')}
          onChange={(v) => setFilterValue('with_companies', v)}
          placeholder="TMDB Company ID"
        />
        <NumberInput
          label="Keyword (ID)"
          value={getFilterValue('with_keywords')}
          onChange={(v) => setFilterValue('with_keywords', v)}
          placeholder="TMDB Keyword ID"
        />
      </FilterSection>
    </div>
  )
}
