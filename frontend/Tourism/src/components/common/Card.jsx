const Card = ({ children, className = "", hover = true, as: Component = "div", ...props }) => (
  <Component className={`ny-card ${hover ? "" : "ny-card-no-hover"} ${className}`} {...props}>
    {children}
  </Component>
)

export default Card
