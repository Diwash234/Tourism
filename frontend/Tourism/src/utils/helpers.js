export const formatCurrency = (amount, currency = "USD") => {
  if (amount === null || amount === undefined || amount === "") return "Unavailable"
  const numericAmount = Number(amount)
  if (!Number.isFinite(numericAmount)) return "Unavailable"
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(numericAmount)
}

export const formatDate = (date) =>
  new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })

export const truncate = (text, length = 100) =>
  text && text.length > length ? `${text.slice(0, length)}...` : text

export const classNames = (...classes) => classes.filter(Boolean).join(" ")