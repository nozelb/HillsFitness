import React, { useState, useCallback } from 'react';
import { Upload, Camera, CheckCircle, ArrowLeft, Loader } from 'lucide-react';
import ApiClient from '../api.js';

interface ImageUploadProps {
  user: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

function ImageUpload({ user, onComplete, onBack }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles([...e.dataTransfer.files]);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles([...e.target.files]);
    }
  };

  const handleFiles = async (files: File[]) => {
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    setUploadedFiles(prev => [...prev, ...imageFiles].slice(0, 2)); // Max 2 files
    
    if (imageFiles.length > 0) {
      await analyzeImage(imageFiles[0]);
    }
  };

  const analyzeImage = async (file: File) => {
    setLoading(true);
    setError('');
    
    try {
      const result = await ApiClient.uploadImage(file, user.access_token);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    if (analysis) {
      onComplete(analysis);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center mb-6">
          <button
            onClick={onBack}
            className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Upload Your Photos</h2>
            <p className="text-gray-600 mt-1">
              Upload front and side photos for accurate physique analysis
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div
            className={`
              relative border-2 border-dashed rounded-lg p-8 text-center transition-all
              ${dragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            <div className="space-y-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drop your photos here, or click to browse
                </p>
                <p className="text-gray-600">
                  PNG, JPG up to 10MB each. Maximum 2 photos.
                </p>
              </div>
            </div>
          </div>

          {/* Photo guidelines */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="font-medium text-blue-900 mb-3 flex items-center">
              <Camera className="h-5 w-5 mr-2" />
              Photo Guidelines
            </h3>
            <ul className="text-blue-800 text-sm space-y-2">
              <li>• Stand straight with arms at your sides</li>
              <li>• Wear fitted clothing or minimal clothing</li>
              <li>• Use good lighting and plain background</li>
              <li>• Take one front-facing and one side-facing photo</li>
            </ul>
          </div>

          {/* Uploaded files */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium text-gray-900">Uploaded Photos</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4 flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                    <span className="text-sm text-gray-700 truncate">{file.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis results */}
          {loading && (
            <div className="bg-yellow-50 rounded-lg p-6 text-center">
              <Loader className="h-8 w-8 text-yellow-600 mx-auto mb-3 animate-spin" />
              <p className="text-yellow-800 font-medium">Analyzing your physique...</p>
              <p className="text-yellow-700 text-sm mt-1">This may take a few moments</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {analysis && (
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="font-medium text-green-900 mb-3 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                Analysis Complete
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-700">Shoulder Width:</span>
                  <span className="font-medium text-green-900 ml-2">{analysis.shoulder_cm.toFixed(1)} cm</span>
                </div>
                <div>
                  <span className="text-green-700">Waist:</span>
                  <span className="font-medium text-green-900 ml-2">{analysis.waist_cm.toFixed(1)} cm</span>
                </div>
                <div>
                  <span className="text-green-700">Hip:</span>
                  <span className="font-medium text-green-900 ml-2">{analysis.hip_cm?.toFixed(1) || 'N/A'} cm</span>
                </div>
                <div>
                  <span className="text-green-700">Body Fat Est.:</span>
                  <span className="font-medium text-green-900 ml-2">{analysis.body_fat_estimate.toFixed(1)}%</span>
                </div>
              </div>
              <p className="text-green-700 text-xs mt-3">
                Confidence: {(analysis.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
          )}

          {/* Continue button */}
          {analysis && (
            <div className="flex justify-end">
              <button
                onClick={handleContinue}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Continue to Data Entry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImageUpload;