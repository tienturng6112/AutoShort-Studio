import os
import uuid
import httpx
import hashlib
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from backend.app.core.config import settings

class AssetService:
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir).resolve()
        if not self.assets_dir.exists():
            self.assets_dir = Path("../assets").resolve()
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def _generate_gradient_card(self, keywords: str, filepath: Path, width: int = 1080, height: int = 1920):
        """Generates a premium gradient image based on the keyword hash."""
        # Use MD5 hash of keywords to consistently choose colors
        h_val = int(hashlib.md5(keywords.encode("utf-8")).hexdigest(), 16)
        hue1 = h_val % 360
        hue2 = (hue1 + 120) % 360
        
        # Create base image
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        
        # HSL to RGB conversion helper
        def hsl_to_rgb(h: float, s: float, l: float) -> tuple:
            # Simple conversion
            c = (1.0 - abs(2.0 * l - 1.0)) * s
            x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
            m = l - c / 2.0
            if 0 <= h < 60:
                r, g, b = c, x, 0
            elif 60 <= h < 120:
                r, g, b = x, c, 0
            elif 120 <= h < 180:
                r, g, b = 0, c, x
            elif 180 <= h < 240:
                r, g, b = 0, x, c
            elif 240 <= h < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

        color1 = hsl_to_rgb(hue1, 0.7, 0.25) # Sleek dark modes
        color2 = hsl_to_rgb(hue2, 0.7, 0.15)
        
        # Vertical gradient interpolation
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        # Draw some soft visual geometric grid elements for extra tech aesthetic
        # Horizontal grids
        grid_color = (255, 255, 255, 10)
        grid_draw = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(grid_draw)
        
        for i in range(1, 10):
            y_pos = int(height * (i / 10))
            g_draw.line([(0, y_pos), (width, y_pos)], fill=(255, 255, 255, 15), width=2)
            
        for i in range(1, 6):
            x_pos = int(width * (i / 6))
            g_draw.line([(x_pos, 0), (x_pos, height)], fill=(255, 255, 255, 15), width=2)
            
        # Composite layers
        img = Image.alpha_composite(img.convert("RGBA"), grid_draw).convert("RGB")
        img.save(filepath, "JPEG", quality=90)

    async def search_and_download(
        self,
        keywords: str,
        project_id: str,
        asset_type: str = "image",
        pexels_key: Optional[str] = None,
        pixabay_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Search and download stock asset. 
        Returns tuple: (asset_path, source_type)
        """
        filename = f"asset_{project_id}_{uuid.uuid4().hex[:8]}"
        ext = ".mp4" if asset_type == "video" else ".jpg"
        filepath = self.assets_dir / (filename + ext)
        
        # 1. Try Pexels if key exists
        if pexels_key:
            try:
                headers = {"Authorization": pexels_key}
                async with httpx.AsyncClient() as client:
                    if asset_type == "video":
                        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(keywords)}&per_page=1"
                        r = await client.get(url, headers=headers, timeout=15.0)
                        if r.status_code == 200:
                            data = r.json()
                            videos = data.get("videos", [])
                            if videos:
                                # Get best quality download link
                                video_files = videos[0].get("video_files", [])
                                # Sort by width descending but filter out 4K if too large
                                video_files = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
                                download_url = video_files[0].get("link")
                                if download_url:
                                    dl_r = await client.get(download_url, timeout=60.0)
                                    if dl_r.status_code == 200:
                                        with open(filepath, "wb") as f:
                                            f.write(dl_r.content)
                                        return str(filepath.resolve()), "pexels_video"
                    else:
                        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
                        r = await client.get(url, headers=headers, timeout=15.0)
                        if r.status_code == 200:
                            data = r.json()
                            photos = data.get("photos", [])
                            if photos:
                                download_url = photos[0].get("src", {}).get("large2x") or photos[0].get("src", {}).get("large")
                                if download_url:
                                    dl_r = await client.get(download_url, timeout=30.0)
                                    if dl_r.status_code == 200:
                                        with open(filepath, "wb") as f:
                                            f.write(dl_r.content)
                                        return str(filepath.resolve()), "pexels_image"
            except Exception as e:
                print(f"Pexels search failed for '{keywords}': {e}")
                
        # 2. Try Pixabay if key exists (Pixabay only provides easy photos search in basic endpoint)
        if pixabay_key and asset_type == "image":
            try:
                url = f"https://pixabay.com/api/?key={pixabay_key}&q={urllib.parse.quote(keywords)}&image_type=photo&per_page=3"
                async with httpx.AsyncClient() as client:
                    r = await client.get(url, timeout=15.0)
                    if r.status_code == 200:
                        data = r.json()
                        hits = data.get("hits", [])
                        if hits:
                            download_url = hits[0].get("largeImageURL") or hits[0].get("webformatURL")
                            if download_url:
                                dl_r = await client.get(download_url, timeout=30.0)
                                if dl_r.status_code == 200:
                                    with open(filepath, "wb") as f:
                                        f.write(dl_r.content)
                                    return str(filepath.resolve()), "pixabay_image"
            except Exception as e:
                print(f"Pixabay search failed for '{keywords}': {e}")

        # 3. Offline fallback / Unsplash fallback for images
        if asset_type == "image":
            # Attempt to pull from Unsplash source or generate local Pillow card
            try:
                # Check online connectivity with a quick request
                unsplash_url = f"https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1080&q=80"
                # If we want a customized card:
                self._generate_gradient_card(keywords, filepath)
                return str(filepath.resolve()), "generated_gradient"
            except Exception as e:
                print(f"Gradient generation failed: {e}")
                # absolute fallback
                self._generate_gradient_card("default fallback", filepath)
                return str(filepath.resolve()), "generated_gradient"
        else:
            # Video fallback: Render a static visual card since we cannot easily download a fallback video offline
            filepath_img = filepath.with_suffix(".jpg")
            self._generate_gradient_card(keywords, filepath_img)
            return str(filepath_img.resolve()), "generated_gradient_image_fallback"
