export function exportToCsv(
  filename: string,
  rows: Record<string, unknown>[]
): void {
  if (!rows.length) return

  const headers = Object.keys(rows[0])
  const csvLines = [
    headers.join(","),
    ...rows.map(row =>
      headers.map(h => {
        const val = row[h]
        // Wrap in quotes if contains comma, newline, or quote
        const str = val === null || val === undefined ? "" : String(val)
        return str.includes(",") || str.includes("\n") || str.includes('"')
          ? `"${str.replace(/"/g, '""')}"`
          : str
      }).join(",")
    )
  ]

  const blob = new Blob([csvLines.join("\n")], { type: "text/csv" })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement("a")
  a.href     = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
