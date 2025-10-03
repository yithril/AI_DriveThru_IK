'use client'

import { useState } from 'react'

export default function AdminImport() {
  const [excelFile, setExcelFile] = useState<File | null>(null)
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [overwrite, setOverwrite] = useState(false)
  const [generateAudio, setGenerateAudio] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')

  const handleImageFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setImageFiles(files)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!excelFile) return

    setLoading(true)
    setResult('')

    try {
      // Create form data
      const formData = new FormData()
      formData.append('excel_file', excelFile)
      
      // Add image files
      imageFiles.forEach((file) => {
        formData.append('images', file)
      })
      
      formData.append('overwrite', overwrite.toString())
      formData.append('generate_audio', generateAudio.toString())

      // Get API base URL
      const apiBaseUrl = '' // Use relative URLs with Next.js rewrite

      // Submit to backend
      const response = await fetch(`${apiBaseUrl}/api/admin/import`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        // Extract restaurant ID from response
        const restaurantId = data.restaurant_id || data.data?.restaurant_id
        const restaurantName = data.restaurant_name || data.data?.restaurant_name
        
        let resultMessage = `✅ Import successful!\n`
        if (restaurantId) {
          resultMessage += `\n🏪 Restaurant ID: ${restaurantId}\n`
          resultMessage += `📝 Restaurant Name: ${restaurantName || 'Unknown'}\n`
          resultMessage += `\n📋 Frontend Configuration:\n`
          resultMessage += `Set NEXT_PUBLIC_RESTAURANT_ID=${restaurantId} in your environment variables\n`
        }
        
        if (data.data) {
          resultMessage += `\n📊 Import Summary:\n`
          resultMessage += `- Categories: ${data.data.categories_created || 0}\n`
          resultMessage += `- Menu Items: ${data.data.menu_items_created || 0}\n`
          resultMessage += `- Ingredients: ${data.data.ingredients_created || 0}\n`
          resultMessage += `- Tags: ${data.data.tags_created || 0}\n`
        }
        
        setResult(resultMessage)
      } else {
        setResult(`❌ Import failed: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      setResult(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Import Restaurant Data</h1>
        <p className="mt-1 text-sm text-gray-600">
          Import menu items, ingredients, and other restaurant data from Excel files
        </p>
      </div>

      {/* Import Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Excel File */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Excel File
            </label>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setExcelFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Upload an Excel file with restaurant data including menu items, ingredients, and categories
            </p>
          </div>

          {/* Image Files */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Image Files (Optional)
            </label>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleImageFilesChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
            {imageFiles.length > 0 && (
              <p className="mt-2 text-sm text-gray-600">
                {imageFiles.length} image(s) selected
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Upload images for menu items (will be matched by filename)
            </p>
          </div>

          {/* Options */}
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="overwrite"
                checked={overwrite}
                onChange={(e) => setOverwrite(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="overwrite" className="ml-2 block text-sm text-gray-900">
                Overwrite existing data
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="generateAudio"
                checked={generateAudio}
                onChange={(e) => setGenerateAudio(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="generateAudio" className="ml-2 block text-sm text-gray-900">
                Generate audio phrases
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={loading || !excelFile}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Importing...' : 'Import Restaurant Data'}
            </button>
          </div>
        </form>

        {/* Result */}
        {result && (
          <div className="mt-6 p-4 bg-gray-100 rounded-md">
            <pre className="text-sm whitespace-pre-wrap">{result}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
