import { useState } from "react"
import { FiSearch } from "react-icons/fi"

const SearchBar = ({ placeholder = "Search destinations...", onSearch, className = "" }) => {
  const [query, setQuery] = useState("")

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch?.(query)
  }

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="input-field pl-11"
      />
    </form>
  )
}

export default SearchBar