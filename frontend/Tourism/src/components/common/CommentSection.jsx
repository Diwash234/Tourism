import { useState, useCallback } from "react"
import { FiMessageCircle, FiSend, FiMoreVertical, FiTrash2, FiEdit2 } from "react-icons/fi"
import { useAuth } from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import Avatar from "./Avatar"

/**
 * Comment section with add, edit, delete, and reply functionality.
 */
export default function CommentSection({
  targetType: _targetType = "destination",
  targetId: _targetId,
  comments = [],
  onSubmit,
  onEdit,
  onDelete,
  className = "",
}) {
  const { isAuthenticated, user } = useAuth()
  const { addToast } = useToast()
  const [newComment, setNewComment] = useState("")
  const [editingId, setEditingId] = useState(null)
  const [editText, setEditText] = useState("")
  const [replyingTo, setReplyingTo] = useState(null)
  const [replyText, setReplyText] = useState("")
  const [menuOpen, setMenuOpen] = useState(null)

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return
    if (!isAuthenticated) {
      addToast("Please login to comment", "warning")
      return
    }
    try {
      await onSubmit?.(newComment.trim())
      setNewComment("")
    } catch {
      addToast("Failed to post comment", "error")
    }
  }, [newComment, isAuthenticated, onSubmit, addToast])

  const handleEdit = useCallback(async (commentId) => {
    if (!editText.trim()) return
    try {
      await onEdit?.(commentId, editText.trim())
      setEditingId(null)
      setEditText("")
    } catch {
      addToast("Failed to update comment", "error")
    }
  }, [editText, onEdit, addToast])

  const handleDelete = useCallback(async (commentId) => {
    try {
      await onDelete?.(commentId)
      setMenuOpen(null)
    } catch {
      addToast("Failed to delete comment", "error")
    }
  }, [onDelete, addToast])

  const handleReply = useCallback(async (parentId) => {
    if (!replyText.trim()) return
    try {
      await onSubmit?.(replyText.trim(), parentId)
      setReplyingTo(null)
      setReplyText("")
    } catch {
      addToast("Failed to post reply", "error")
    }
  }, [replyText, onSubmit, addToast])

  return (
    <div className={`space-y-4 ${className}`}>
      <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <FiMessageCircle size={16} />
        Comments ({comments.length})
      </h3>

      {/* Comment Form */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <Avatar name={user?.first_name || "Guest"} size="sm" />
        <div className="flex-1 relative">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={isAuthenticated ? "Write a comment..." : "Login to comment..."}
            className="w-full text-sm rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 pr-10 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={!isAuthenticated}
          />
          <button
            type="submit"
            disabled={!newComment.trim() || !isAuthenticated}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Send comment"
          >
            <FiSend size={16} />
          </button>
        </div>
      </form>

      {/* Comments List */}
      <div className="space-y-3">
        {comments.map((comment) => (
          <div key={comment.id} className="group">
            <div className="flex gap-3">
              <Avatar name={comment.user_name || "User"} size="sm" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-gray-900 dark:text-white">
                    {comment.user_name}
                  </span>
                  <span className="text-[10px] text-gray-400">{comment.created_at}</span>
                </div>

                {editingId === comment.id ? (
                  <div className="mt-1 flex gap-2">
                    <input
                      type="text"
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => handleEdit(comment.id)}
                      className="px-2 py-1 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => { setEditingId(null); setEditText("") }}
                      className="px-2 py-1 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">{comment.text}</p>
                )}

                {/* Reply */}
                {replyingTo === comment.id && (
                  <div className="mt-2 flex gap-2">
                    <input
                      type="text"
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder="Write a reply..."
                      className="flex-1 text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => handleReply(comment.id)}
                      className="px-2 py-1 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                    >
                      Reply
                    </button>
                    <button
                      type="button"
                      onClick={() => { setReplyingTo(null); setReplyText("") }}
                      className="px-2 py-1 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {/* Menu */}
              {isAuthenticated && comment.user_id === user?.id && (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setMenuOpen(menuOpen === comment.id ? null : comment.id)}
                    className="p-1 rounded text-gray-300 hover:text-gray-500 opacity-0 group-hover:opacity-100 transition-all"
                    aria-label="Comment options"
                  >
                    <FiMoreVertical size={14} />
                  </button>
                  {menuOpen === comment.id && (
                    <div className="absolute right-0 top-full mt-1 w-32 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl z-50 py-1">
                      <button
                        type="button"
                        onClick={() => { setEditingId(comment.id); setEditText(comment.text); setMenuOpen(null) }}
                        className="flex w-full items-center gap-2 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                      >
                        <FiEdit2 size={12} /> Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(comment.id)}
                        className="flex w-full items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                      >
                        <FiTrash2 size={12} /> Delete
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
