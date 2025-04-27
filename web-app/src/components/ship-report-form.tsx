"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { MapPin, AlertCircle, Ship, Upload, Check, Camera, LogOut, Star } from "lucide-react"

// Default API endpoint with fallback
const API_ENDPOINT = process.env.SUBMIT_SHIP_ENDPOINT || '/api/submit_ship';

// Add activity types interface
const ACTIVITY_TYPES = [
  { id: 'trespassing', labelKey: 'territorialWatersTrespassing' },
  { id: 'fishing', labelKey: 'illegalFishing' },
  { id: 'pirating', labelKey: 'piratingActivity' },
  { id: 'smuggling', labelKey: 'suspectedSmuggling' },
  { id: 'environmental', labelKey: 'environmentalViolation' },
  { id: 'other', labelKey: 'otherSuspiciousActivity' },
] as const;

// Add vessel headings interface
const VESSEL_HEADINGS = [
  { id: 'N', labelKey: 'north' },
  { id: 'E', labelKey: 'east' },
  { id: 'S', labelKey: 'south' },
  { id: 'W', labelKey: 'west' },
  { id: 'docked', labelKey: 'docked' },
  { id: 'stationary', labelKey: 'stationary' },
  { id: 'unknown', labelKey: 'unknown' },
] as const;

// Add vessel registry flags
// This is a list of country flags and their names for a quick lookup
const VESSEL_REGISTRY_FLAGS = [
  { code: '🇺🇸', nameKey: 'United States' },
  { code: '🇬🇧', nameKey: 'United Kingdom' },
  { code: '🇨🇦', nameKey: 'Canada' },
  { code: '🇦🇺', nameKey: 'Australia' },
  { code: '🇳🇿', nameKey: 'New Zealand' },
  { code: '🇯🇵', nameKey: 'Japan' },
  { code: '🇨🇳', nameKey: 'China' },
  { code: '🇷🇺', nameKey: 'Russia' },
  { code: '🇮🇳', nameKey: 'India' },
  { code: '🇧🇷', nameKey: 'Brazil' },
  { code: '🇵🇦', nameKey: 'Panama' },
  { code: '🇱🇷', nameKey: 'Liberia' },
  { code: '🇲🇭', nameKey: 'Marshall Islands' },
  { code: '🇸🇬', nameKey: 'Singapore' },
  { code: '🇳🇴', nameKey: 'Norway' },
  { code: '🇬🇷', nameKey: 'Greece' },
  { code: '🇲🇹', nameKey: 'Malta' },
  { code: '🇨🇾', nameKey: 'Cyprus' },
  { code: '🇮🇹', nameKey: 'Italy' },
  { code: '🇫🇷', nameKey: 'France' },
  { code: '🇩🇪', nameKey: 'Germany' },
  { code: '🇳🇱', nameKey: 'Netherlands' },
  { code: '🇪🇸', nameKey: 'Spain' },
  { code: '🇵🇹', nameKey: 'Portugal' },
  { code: '🇩🇰', nameKey: 'Denmark' },
  { code: '🇸🇪', nameKey: 'Sweden' },
  { code: '🇫🇮', nameKey: 'Finland' },
] as const;

interface ShipReportFormProps {
  user: { id: string; name: string; score: number } | null
  onLogout: () => void
  t: any
}

export default function ShipReportForm({ user, onLogout, t }: ShipReportFormProps) {
  const [description, setDescription] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [isGettingLocation, setIsGettingLocation] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [activityType, setActivityType] = useState<string>('')
  const [vesselHeading, setVesselHeading] = useState<string>('')
  const [vesselRegistry, setVesselRegistry] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)
  const [enrichedReport, setEnrichedReport] = useState<any>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setImage(file)

      // Create preview
      const reader = new FileReader()
      reader.onload = (event) => {
        setImagePreview(event.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const getLocation = () => {
    setIsGettingLocation(true)
    setLocationError(null)

    if (!navigator.geolocation) {
      setLocationError(t("geolocationNotSupported"))
      setIsGettingLocation(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
        setIsGettingLocation(false)
      },
      (error) => {
        setLocationError(t("errorGettingLocation", { error: error.message }))
        setIsGettingLocation(false)
      },
    )
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setIsCameraActive(true)
      }
    } catch (err) {
      console.error("Error accessing camera:", err)
      alert(t("cameraAccessError"))
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setIsCameraActive(false)
  }

  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current
      const canvas = canvasRef.current

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      // Draw the video frame to the canvas
      const context = canvas.getContext("2d")
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert canvas to file
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const file = new File([blob], "camera-photo.jpg", { type: "image/jpeg" })
              setImage(file)
              setImagePreview(canvas.toDataURL("image/jpeg"))
              stopCamera()
            }
          },
          "image/jpeg",
          0.95,
        )
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setFormError(null)

    // Check if either image or location is provided
    if (!image && !location) {
      setFormError(t("eitherImageOrLocationRequired"))
      setIsSubmitting(false)
      return
    }

    try {
      // Create a timestamp 
      const timestamp = new Date().toISOString();
      
      // Convert image to base64 if available
      let base64Image = null;
      if (image) {
        base64Image = await convertImageToBase64(image);
      }
      
      // Prepare the API payload according to the required structure
      const apiPayload = {
        source_account_id: user?.id || "guest",
        timestamp: timestamp,
        latitude: location?.latitude,
        longitude: location?.longitude,
        picture_url: base64Image, // Using base64 image data
        description: description || undefined,
        activity_type: activityType || undefined,
        vessel_heading: vesselHeading || undefined,
        vessel_registry: vesselRegistry || undefined,
      };
      
      console.log("Sending payload to API:", apiPayload);
      
      // Send the API request
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(apiPayload),
      });

      if (!response.ok) {
        let errorMsg = t("failedToSubmitReport")
        try {
          const errData = await response.json()
          if (errData.detail) {
            if (typeof errData.detail === 'string') {
              errorMsg = errData.detail
            } else if (Array.isArray(errData.detail)) {
              // If detail is an array of error objects, join their messages
              errorMsg = errData.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
            } else if (typeof errData.detail === 'object') {
              // If detail is an object, try to extract msg or stringify
              errorMsg = errData.detail.msg || JSON.stringify(errData.detail)
            }
          }
        } catch (e) {}
        setFormError(errorMsg)
        setIsSubmitting(false)
        return
      }

      const data = await response.json();
      console.log("API response:", data);
      setEnrichedReport(data)
      setIsSubmitting(false)
      setIsSuccess(true)

      // Reset form after 3 seconds
      setTimeout(() => {
        setDescription("")
        setImage(null)
        setImagePreview(null)
        setVesselRegistry("")
        setIsSuccess(false)
        setEnrichedReport(null)
      }, 3000)
    } catch (error) {
      console.error("Error submitting form:", error);
      setIsSubmitting(false)
      alert(t("failedToSubmitReport"))
    }
  }

  // Helper function to convert an image file to a base64 string
  const convertImageToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert image to base64'));
        }
      };
      reader.onerror = () => {
        reject(new Error('Failed to read image file'));
      };
      reader.readAsDataURL(file);
    });
  };

  // Function to render stars based on score
  const renderStars = (score: number) => {
    const stars = [];
    const maxDisplayedStars = 5;
    const fullStars = Math.min(score, maxDisplayedStars);
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <Star key={i} className="h-6 w-6 fill-yellow-400 text-yellow-400" />
      );
    }
    
    // Add empty stars to complete the set
    for (let i = fullStars; i < maxDisplayedStars; i++) {
      stars.push(
        <Star key={i + 'empty'} className="h-6 w-6 text-gray-300" />
      );
    }
    
    return stars;
  };

  // Clean up camera stream on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [])

  return (
    <div className="space-y-4">
      {isSuccess ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-600" />
            <h4 className="font-medium">{t("success")}</h4>
          </div>
          <p className="text-sm mt-1">{t("reportSubmittedSuccessfully")}</p>
        </div>
      ) : isCameraActive ? (
        <div className="space-y-4">
          <div className="relative">
            <video ref={videoRef} autoPlay playsInline className="w-full rounded-md border border-gray-300" />
            <canvas ref={canvasRef} className="hidden" />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={takePhoto}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Camera className="h-4 w-4" />
              {t("takePhoto")}
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50"
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>{t("note")}</strong>: {t("eitherImageOrLocationRequired")}
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-label">
              {t("sendImage")}
            </label>
            {imagePreview ? (
              <div className="border rounded-md p-2">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-h-40 mx-auto object-contain rounded-md"
                />
                <div className="flex gap-2 mt-2">
                  <button
                    type="button"
                    className="flex-1 px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50"
                    onClick={() => {
                      setImage(null)
                      setImagePreview(null)
                      if (fileInputRef.current) fileInputRef.current.value = ""
                    }}
                  >
                    {t("remove")}
                  </button>
                  <button
                    type="button"
                    className="flex-1 px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {t("change")}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  type="button"
                  className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4" />
                  {t("uploadImage")}
                </button>
                <button
                  type="button"
                  className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2"
                  onClick={startCamera}
                >
                  <Camera className="h-4 w-4" />
                  {t("takePhoto")}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageChange}
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-label">
              {t("sendLocation")}
            </label>
            {location ? (
              <div className="p-3 bg-gray-100 rounded-md">
                <div className="flex items-center text-sm">
                  <MapPin className="h-4 w-4 mr-2 text-gray-500" />
                  <span>
                    Lat: {location.latitude.toFixed(6)}, Long: {location.longitude.toFixed(6)}
                  </span>
                </div>
              </div>
            ) : (
              <button
                type="button"
                className="w-full border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={getLocation}
                disabled={isGettingLocation}
              >
                <MapPin className="h-4 w-4" />
                {isGettingLocation ? t("gettingLocation") : t("getCurrentLocation")}
              </button>
            )}

            {locationError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <h4 className="font-medium">{t("error")}</h4>
                </div>
                <p className="text-sm mt-1">{locationError}</p>
              </div>
            )}
          </div>

          {/* Activity Type Dropdown */}
          <div className="space-y-1">
            <label htmlFor="activityType" className="block text-sm font-medium text-label">
              {t("activityType")}
            </label>
            <select
              id="activityType"
              value={activityType}
              onChange={(e) => setActivityType(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">{t("selectActivityType")}</option>
              {ACTIVITY_TYPES.map(type => (
                <option key={type.id} value={type.id}>
                  {t(type.labelKey)}
                </option>
              ))}
            </select>
          </div>

          {/* Vessel Heading Dropdown */}
          <div className="space-y-1">
            <label htmlFor="vesselHeading" className="block text-sm font-medium text-label">
              {t("vesselHeading")}
            </label>
            <select
              id="vesselHeading"
              value={vesselHeading}
              onChange={(e) => setVesselHeading(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">{t("selectVesselHeading")}</option>
              {VESSEL_HEADINGS.map(heading => (
                <option key={heading.id} value={heading.id}>
                  {t(heading.labelKey)}
                </option>
              ))}
            </select>
          </div>

          {/* Vessel Registry Flag Dropdown */}
          <div className="space-y-1">
            <label htmlFor="vesselRegistry" className="block text-sm font-medium text-label">
              {t("vesselRegistryFlag")}
            </label>
            <select
              id="vesselRegistry"
              value={vesselRegistry}
              onChange={(e) => setVesselRegistry(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">{t("selectRegistryFlag")}</option>
              {VESSEL_REGISTRY_FLAGS.map(flag => (
                <option key={flag.code} value={flag.code}>
                  {flag.code} {t(flag.nameKey)}
                </option>
              ))}
            </select>
          </div>

          {/* Details textarea now comes after activity type */}
          <div className="space-y-1">
            <label htmlFor="description" className="block text-sm font-medium text-label" style={{ color: 'var(--label-color)', opacity: 1 }}>
              {t("provideDetails")}
            </label>
            <textarea
              id="description"
              className="w-full rounded-md border border-custom px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors placeholder-[color:var(--foreground)] placeholder-opacity-70"
              placeholder={t("describeShip")}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              style={{ color: 'var(--input-text)', background: 'var(--input-bg)' }}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting || (!image && !location)}
            className="w-full px-4 py-2 rounded-md transition-colors bg-[var(--button-bg)] text-[var(--button-text)] hover:bg-[var(--button-hover-bg)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style={{ color: isSubmitting || (!image && !location) ? '#a1a1aa' : 'var(--button-text)', background: isSubmitting || (!image && !location) ? '#e5e7eb' : 'var(--button-bg)' }}
          >
            <Ship className="h-4 w-4" />
            {isSubmitting ? t("submitting") : t("submitReport")}
          </button>

          {formError && (
            <div className="bg-error border border-custom rounded-lg p-4 mt-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-error" />
                <h4 className="font-medium text-error">{t("error")}</h4>
              </div>
              <p className="text-sm mt-1 text-error">{formError}</p>
            </div>
          )}

          {isSuccess && enrichedReport && (
            <div className="mt-4 p-4 bg-green-100 border border-green-300 rounded">
              <h3 className="font-bold mb-2">{t('reportSubmitted')}</h3>
              <ul className="text-sm">
                {enrichedReport.report_number && (
                  <li><strong>{t('reportNumber')}:</strong> {enrichedReport.report_number}</li>
                )}
                {enrichedReport.trust_score !== undefined && (
                  <li><strong>{t('trustScore')}:</strong> {enrichedReport.trust_score}</li>
                )}
                {enrichedReport.ais_neighbours && (
                  <li><strong>{t('aisNeighbours')}:</strong> {enrichedReport.ais_neighbours.join(', ')}</li>
                )}
                {enrichedReport.visibility !== undefined && (
                  <li><strong>{t('visibility')}:</strong> {enrichedReport.visibility}</li>
                )}
              </ul>
            </div>
          )}

          {user?.id === "guest" && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <h4 className="font-medium">{t("guestMode")}</h4>
              </div>
              <p className="text-sm mt-1">{t("reportingAsGuest")}</p>
            </div>
          )}

          {/* Maritime Observer Status and User Info */}
          <div className="mt-8 pt-4 border-t border-custom">
            {/* Observer Status */}
            {user && (
              <div className="mb-4 bg-gradient-to-b from-blue-50 to-white dark:from-blue-900 dark:to-secondary p-4 rounded-lg border border-blue-100 dark:border-blue-900">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-300 mb-1 text-center">{t("maritimeObserverStatus")}</p>
                
                <div className="flex justify-center gap-1 mb-1">
                  {renderStars(user.score)}
                </div>
                
                {user.score > 0 ? (
                  <p className="text-sm text-center font-medium text-gray-700 dark:text-gray-100 mt-1">
                    {user.score >= 5 ? 
                      t("maritimeSecuritySpecialist") : 
                      user.score >= 3 ? 
                        t("verifiedCoastalMonitor") : 
                        t("qualifiedMaritimeObserver")}
                  </p>
                ) : (
                  <p className="text-xs text-center text-gray-500 dark:text-gray-400 mt-1">
                    {t("establishCredentials")}
                  </p>
                )}
              </div>
            )}
            
            {/* User info and logout */}
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-foreground opacity-70">{t("loggedInAs")}</p>
                <p className="text-sm font-semibold text-foreground">{user?.name}</p>
              </div>
              <button
                onClick={onLogout}
                className="px-3 py-1.5 text-sm border border-custom rounded-md hover:bg-secondary transition-colors flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                {t("logout")}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}