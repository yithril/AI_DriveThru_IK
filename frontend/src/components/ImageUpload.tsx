'use client'

import { useState, useRef, useCallback } from 'react'
import { apiClient } from '@/lib/api'

interface ImageUploadProps {
  onImageUpload: (imageUrl: string, fileData: any) => void
  restaurantId: number
  disabled?: boolean
  className?: string
}

export default function ImageUpload({ 
  onImageUpload, 
  restaurantId, 
  disabled = false,
  className = ''
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    const imageFile = files.find(file => file.type.startsWith('image/'))
    
    if (imageFile) {
      handleFileSelect(imageFile)
    } else {
      setError('Please select an image file')
    }
  }, [disabled])

  const handleFileSelect = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setError('File size must be less than 10MB')
      return
    }

    setError(null)
    setUploading(true)
    setUploadProgress(0)

    try {
      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)

      // Upload to backend using API client
      const result = await apiClient.uploadImage(file, restaurantId)
      
      if (result.success) {
        onImageUpload(result.data.image_url, result.data)
        setUploadProgress(100)
      } else {
        throw new Error(result.message || 'Upload failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setPreview(null)
    } finally {
      setUploading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleClick = () => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click()
    }
  }

  const handleClear = () => {
    setPreview(null)
    setError(null)
    setUploadProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled || uploading ? 'opacity-50 cursor-not-allowed' : ''}
          ${error ? 'border-red-300 bg-red-50' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled || uploading}
        />

        {preview ? (
          <div className="space-y-4">
            <img
              src={preview}
              alt="Preview"
              className="mx-auto h-32 w-32 object-cover rounded-lg"
            />
            <div className="text-sm text-gray-600">
              {uploading ? (
                <div className="space-y-2">
                  <div className="text-indigo-600">Uploading...</div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-4">
                  <span className="text-green-600">✓ Uploaded successfully</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleClear()
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-indigo-600 hover:text-indigo-500">
                  Click to upload
                </span>{' '}
                or drag and drop
              </p>
              <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
          {error}
        </div>
      )}

      {/* Upload Instructions */}
      <div className="text-xs text-gray-500">
        <p>• Supported formats: PNG, JPG, JPEG, GIF</p>
        <p>• Maximum file size: 10MB</p>
        <p>• Images will be automatically resized and optimized</p>
      </div>
    </div>
  )
}
