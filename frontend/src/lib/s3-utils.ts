/**
 * Utility functions for constructing S3 URLs
 */

/**
 * Construct S3 URL for canned audio phrases
 * @param phrase - The phrase type (e.g., 'come_again')
 * @param restaurantId - Restaurant ID (optional, defaults to env var)
 * @returns Full S3 URL for the canned phrase
 */
export function getCannedPhraseUrl(phrase: string, restaurantId?: number): string {
  const s3BucketUrl = process.env.NEXT_PUBLIC_S3_BUCKET_URL || 'https://ai-drivethru-files-5ddf24fb.s3.us-east-1.amazonaws.com';
  const rid = restaurantId || process.env.NEXT_PUBLIC_RESTAURANT_ID || '1';
  
  return `${s3BucketUrl}/canned-phrases/restaurant-${rid}/${phrase}.mp3`;
}

/**
 * Construct S3 URL for restaurant images
 * @param imageUrl - The image filename
 * @param restaurantId - Restaurant ID (optional, defaults to env var)
 * @returns Full S3 URL for the image
 */
export function getImageUrl(imageUrl: string, restaurantId?: number): string {
  const s3BucketUrl = process.env.NEXT_PUBLIC_S3_BUCKET_URL || 'https://ai-drivethru-files-5ddf24fb.s3.us-east-1.amazonaws.com';
  const rid = restaurantId || process.env.NEXT_PUBLIC_RESTAURANT_ID || '1';
  
  return `${s3BucketUrl}/restaurants/${rid}/images/${imageUrl}`;
}

/**
 * Play a canned audio phrase
 * @param phrase - The phrase type (e.g., 'come_again')
 * @param restaurantId - Restaurant ID (optional, defaults to env var)
 * @returns Promise that resolves when audio finishes playing
 */
export function playCannedPhrase(phrase: string, restaurantId?: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const audioUrl = getCannedPhraseUrl(phrase, restaurantId);
    const audio = new Audio(audioUrl);
    
    audio.onended = () => resolve();
    audio.onerror = () => reject(new Error(`Failed to play audio: ${audioUrl}`));
    
    audio.play().catch(reject);
  });
}
