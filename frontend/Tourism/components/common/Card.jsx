const Card = ({ children, className = "", hover = true }) => (
  <div className={`card-base p-5 ${hover ? "" : "hover:shadow-none"} ${className}`}>
    {children}
  </div>
)

export default Card