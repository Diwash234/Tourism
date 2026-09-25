import { cn } from "../../utils/cn"

/**
 * Shared calm card surface. The former border-beam treatment competed with
 * the Nepal Yatra content hierarchy; callers now get the same restrained card
 * language as destination, package and editorial cards.
 */
export const BorderBeamCard = ({ children, className = "", hoverEffect = true }) => (
  <div className={cn("ny-card overflow-hidden", hoverEffect && "transition duration-200 hover:-translate-y-0.5", className)}>
    {children}
  </div>
)

export default BorderBeamCard
