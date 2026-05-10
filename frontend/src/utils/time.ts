/**
 * 时区感知的时间格式化工具。
 *
 * 后端 API 返回的 ISO 时间字符串均以 Z 后缀标记为 UTC，
 * 此工具负责统一转换为用户本地时区显示。
 */

/**
 * 将 ISO 时间字符串格式化为用户本地时间字符串。
 *
 * @param isoStr - ISO 8601 时间字符串（如 "2026-05-10T12:00:00Z"），或 null/undefined
 * @param fallback - 值为空时的替代文字，默认 "-"
 * @returns 格式化后的本地时间字符串
 */
export function formatDateTime(isoStr: string | null | undefined, fallback = "-"): string {
  if (!isoStr) return fallback

  // 构建 Date 对象时明确告知这是 UTC 时间（通过 Z 或 +00:00 后缀）
  // 如果后端返回的字符串没有 Z，补齐后再解析
  const normalized = isoStr.endsWith("Z") || isoStr.includes("+") ? isoStr : isoStr + "Z"
  const date = new Date(normalized)

  if (isNaN(date.getTime())) return fallback

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

/**
 * 将 ISO 时间字符串格式化为相对时间（如 "3 分钟前"）。
 *
 * @param isoStr - ISO 8601 时间字符串
 * @param fallback - 值为空时的替代文字
 * @returns 相对时间字符串
 */
export function relativeTime(isoStr: string | null | undefined, fallback = "-"): string {
  if (!isoStr) return fallback

  const normalized = isoStr.endsWith("Z") || isoStr.includes("+") ? isoStr : isoStr + "Z"
  const date = new Date(normalized)
  if (isNaN(date.getTime())) return fallback

  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)

  if (diffSec < 60) return "刚刚"
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 30) return `${diffDay} 天前`

  return formatDateTime(isoStr, fallback)
}
