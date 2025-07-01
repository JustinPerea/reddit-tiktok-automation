"""
FastAPI web application for Reddit-to-TikTok automation system.
Provides a user-friendly web interface for content processing and video creation.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from processors.content_processor import ContentProcessor
from generators.hybrid_tts import HybridTTSEngine
from generators.video_generator import VideoGenerator, VideoConfig, VideoFormat, BackgroundType
from config.settings import get_settings
from utils.logger import setup_logging, get_logger


# Setup logging
setup_logging()
logger = get_logger("WebApp")

# Initialize processors
content_processor = ContentProcessor()
tts_engine = HybridTTSEngine()
video_generator = VideoGenerator()
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Reddit-to-TikTok Automation",
    description="AI-powered content processing and video generation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Pydantic models
class ContentRequest(BaseModel):
    text: str
    source_url: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    provider: Optional[str] = None
    voice: Optional[str] = None
    speed: float = 1.0


class VideoRequest(BaseModel):
    text: str
    audio_filename: str
    background_type: Optional[str] = "geometric_patterns"
    video_format: Optional[str] = "tiktok"


class ProcessingResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit-to-TikTok Automation</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover { transition: transform 0.2s; }
        .card-hover:hover { transform: translateY(-2px); }
        .pulse-ring { animation: pulse-ring 1.25s cubic-bezier(0.215, 0.61, 0.355, 1) infinite; }
        @keyframes pulse-ring {
            0% { transform: scale(.33); }
            80%, 100% { opacity: 0; }
        }
        .quality-bar {
            background: linear-gradient(to right, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            height: 8px;
            border-radius: 4px;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <div class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-video text-2xl"></i>
                    <h1 class="text-2xl font-bold">Reddit-to-TikTok Automation</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="bg-green-500 px-3 py-1 rounded-full text-sm">$0/month TTS</span>
                    <span id="status-indicator" class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-green-400 rounded-full"></div>
                        <span class="text-sm">System Ready</span>
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="container mx-auto px-6 py-8">
        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            <!-- Input Panel -->
            <div class="space-y-6">
                <!-- Content Input -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-edit text-blue-500"></i>
                        <h2 class="text-xl font-semibold">Content Input</h2>
                    </div>
                    
                    <textarea
                        id="content-input"
                        placeholder="Paste your Reddit story here... (AITA posts work great!)"
                        class="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        oninput="analyzeContent()"
                    ></textarea>
                    
                    <div class="mt-4 flex flex-wrap gap-2">
                        <button onclick="loadSampleContent()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
                            <i class="fas fa-file-alt mr-2"></i>Load Sample
                        </button>
                        <button onclick="clearContent()" class="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition">
                            <i class="fas fa-trash mr-2"></i>Clear
                        </button>
                    </div>
                </div>

                <!-- Quality Analysis -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-chart-line text-green-500"></i>
                        <h2 class="text-xl font-semibold">Quality Analysis</h2>
                    </div>
                    
                    <div id="quality-results" class="space-y-4">
                        <div class="text-gray-500 text-center py-8">
                            <i class="fas fa-brain text-4xl mb-2"></i>
                            <p>Enter content to see AI analysis</p>
                        </div>
                    </div>
                </div>

                <!-- TTS Configuration -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-microphone text-purple-500"></i>
                        <h2 class="text-xl font-semibold">Voice Settings</h2>
                    </div>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">TTS Provider</label>
                            <select id="tts-provider" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="auto">Auto-Select (Recommended)</option>
                                <option value="gtts">Google TTS (Fast & Reliable)</option>
                                <option value="edge_tts">Microsoft Edge TTS (Premium Quality)</option>
                                <option value="coqui">Coqui TTS (Voice Cloning)</option>
                                <option value="pyttsx3">System TTS (Offline Fallback)</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Voice Style</label>
                            <select id="voice-style" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="auto">Auto-Select Based on Content</option>
                                <option value="professional">Professional (Workplace Stories)</option>
                                <option value="friendly">Friendly (Family Stories)</option>
                                <option value="authoritative">Authoritative (AITA Stories)</option>
                                <option value="casual">Casual (TIFU Stories)</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Speech Speed: <span id="speed-value">1.0x</span></label>
                            <input type="range" id="speech-speed" min="0.5" max="2.0" step="0.1" value="1.0" class="w-full" oninput="updateSpeedValue()">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Output Panel -->
            <div class="space-y-6">
                <!-- Processing Status -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-cogs text-yellow-500"></i>
                        <h2 class="text-xl font-semibold">Processing</h2>
                    </div>
                    
                    <div id="processing-status" class="space-y-4">
                        <button onclick="processContent()" class="w-full bg-blue-500 text-white py-3 px-6 rounded-lg hover:bg-blue-600 transition font-semibold">
                            <i class="fas fa-play mr-2"></i>Generate Audio
                        </button>
                    </div>
                </div>

                <!-- Audio Preview -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-headphones text-indigo-500"></i>
                        <h2 class="text-xl font-semibold">Audio Preview</h2>
                    </div>
                    
                    <div id="audio-preview" class="space-y-4">
                        <div class="text-gray-500 text-center py-8">
                            <i class="fas fa-volume-up text-4xl mb-2"></i>
                            <p>Audio will appear here after processing</p>
                        </div>
                    </div>
                </div>

                <!-- Video Preview -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-film text-red-500"></i>
                        <h2 class="text-xl font-semibold">Video Preview</h2>
                    </div>
                    
                    <div id="video-preview" class="space-y-4">
                        <div class="text-gray-500 text-center py-8">
                            <i class="fas fa-video text-4xl mb-2"></i>
                            <p>Video generation coming soon!</p>
                            <p class="text-sm mt-2">Currently building video pipeline</p>
                        </div>
                    </div>
                </div>

                <!-- Download Options -->
                <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fas fa-download text-green-500"></i>
                        <h2 class="text-xl font-semibold">Download</h2>
                    </div>
                    
                    <div id="download-options" class="space-y-3">
                        <button disabled class="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-lg cursor-not-allowed">
                            <i class="fas fa-file-audio mr-2"></i>Download Audio (MP3)
                        </button>
                        <button disabled class="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-lg cursor-not-allowed">
                            <i class="fas fa-file-video mr-2"></i>Download Video (MP4)
                        </button>
                        <button disabled class="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-lg cursor-not-allowed">
                            <i class="fas fa-file-text mr-2"></i>Download Script (TXT)
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script>
        let currentAnalysis = null;
        let currentAudio = null;

        // Sample content
        const sampleContent = `AITA for refusing to give my sister money for her wedding?

So basically, my sister Sarah (28F) is getting married next month and has been asking everyone in the family for money to help pay for her "dream wedding." The thing is, she's been planning this huge expensive wedding that costs like $50,000 and she and her fiancé only make about $60,000 combined per year.

I (25M) just graduated college and started my first job. I'm making decent money but I'm also paying off student loans and trying to save up to move out of my parents' house. When Sarah asked me for $2,000 to help with the wedding, I told her I couldn't afford it right now.

She completely lost it and started yelling at me, saying I was being selfish and that "family should support each other." She said I was ruining her special day and that I obviously don't care about her happiness. My parents are now pressuring me to give her the money because "it's her wedding and she'll only get married once."

But here's the thing - Sarah has always been terrible with money. She's constantly buying expensive clothes and going on vacations she can't afford, and then asks the family to bail her out. I'm tired of enabling her bad financial decisions.

I told her that if she wanted a cheaper wedding, she could have one, but I'm not going to go into debt to fund her expensive taste. Now half the family is mad at me and saying I'm being an asshole.

AITA for refusing to give my sister money for her wedding?`;

        function loadSampleContent() {
            document.getElementById('content-input').value = sampleContent;
            analyzeContent();
        }

        function clearContent() {
            document.getElementById('content-input').value = '';
            document.getElementById('quality-results').innerHTML = `
                <div class="text-gray-500 text-center py-8">
                    <i class="fas fa-brain text-4xl mb-2"></i>
                    <p>Enter content to see AI analysis</p>
                </div>`;
        }

        function updateSpeedValue() {
            const speed = document.getElementById('speech-speed').value;
            document.getElementById('speed-value').textContent = speed + 'x';
        }

        async function analyzeContent() {
            const content = document.getElementById('content-input').value;
            if (!content.trim()) {
                clearContent();
                return;
            }

            // Show loading state
            document.getElementById('quality-results').innerHTML = `
                <div class="text-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p class="text-gray-600">Analyzing content...</p>
                </div>`;

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: content })
                });

                const result = await response.json();
                currentAnalysis = result.data;
                displayAnalysis(result.data);
            } catch (error) {
                console.error('Error analyzing content:', error);
                document.getElementById('quality-results').innerHTML = `
                    <div class="text-red-500 text-center py-8">
                        <i class="fas fa-exclamation-triangle text-4xl mb-2"></i>
                        <p>Analysis failed. Please try again.</p>
                    </div>`;
            }
        }

        function displayAnalysis(analysis) {
            const qualityScore = analysis.validation.quality_score;
            const qualityPercent = Math.round(qualityScore * 100);
            const qualityColor = qualityScore >= 0.8 ? 'text-green-600' : qualityScore >= 0.6 ? 'text-yellow-600' : 'text-red-600';
            const qualityBg = qualityScore >= 0.8 ? 'bg-green-100' : qualityScore >= 0.6 ? 'bg-yellow-100' : 'bg-red-100';

            document.getElementById('quality-results').innerHTML = `
                <div class="space-y-4">
                    <!-- Overall Quality -->
                    <div class="${qualityBg} rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-semibold ${qualityColor}">Overall Quality Score</span>
                            <span class="text-2xl font-bold ${qualityColor}">${qualityPercent}%</span>
                        </div>
                        <div class="quality-bar relative rounded-full overflow-hidden">
                            <div class="bg-white h-full rounded-full" style="width: ${100-qualityPercent}%; margin-left: ${qualityPercent}%"></div>
                        </div>
                    </div>

                    <!-- Metrics -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 rounded p-3">
                            <div class="text-sm text-gray-600">Word Count</div>
                            <div class="font-semibold">${analysis.validation.word_count}</div>
                        </div>
                        <div class="bg-gray-50 rounded p-3">
                            <div class="text-sm text-gray-600">Story Type</div>
                            <div class="font-semibold capitalize">${analysis.metadata.story_type}</div>
                        </div>
                        <div class="bg-gray-50 rounded p-3">
                            <div class="text-sm text-gray-600">Duration</div>
                            <div class="font-semibold">${analysis.estimated_duration}s</div>
                        </div>
                        <div class="bg-gray-50 rounded p-3">
                            <div class="text-sm text-gray-600">Voice</div>
                            <div class="font-semibold">${analysis.metadata.suggested_voice}</div>
                        </div>
                    </div>

                    <!-- Issues & Recommendations -->
                    ${analysis.validation.issues.length > 0 ? `
                        <div class="bg-red-50 border border-red-200 rounded p-3">
                            <div class="font-semibold text-red-800 mb-2">Issues:</div>
                            <ul class="text-red-700 text-sm space-y-1">
                                ${analysis.validation.issues.map(issue => `<li>• ${issue}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${analysis.validation.recommendations.length > 0 ? `
                        <div class="bg-blue-50 border border-blue-200 rounded p-3">
                            <div class="font-semibold text-blue-800 mb-2">Recommendations:</div>
                            <ul class="text-blue-700 text-sm space-y-1">
                                ${analysis.validation.recommendations.map(rec => `<li>• ${rec}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        async function processContent() {
            const content = document.getElementById('content-input').value;
            if (!content.trim()) {
                alert('Please enter some content first!');
                return;
            }

            const provider = document.getElementById('tts-provider').value;
            const speed = parseFloat(document.getElementById('speech-speed').value);

            // Show processing state
            document.getElementById('processing-status').innerHTML = `
                <div class="text-center py-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p class="text-gray-600">Generating audio...</p>
                    <p class="text-sm text-gray-500">This may take a few moments</p>
                </div>`;

            try {
                const response = await fetch('/api/synthesize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: content,
                        provider: provider === 'auto' ? null : provider,
                        speed: speed
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    displayAudioResult(result.data);
                    document.getElementById('processing-status').innerHTML = `
                        <div class="text-center py-4">
                            <div class="text-green-600 mb-2">
                                <i class="fas fa-check-circle text-2xl"></i>
                            </div>
                            <p class="text-green-600 font-semibold">Audio generated successfully!</p>
                            <button onclick="processContent()" class="mt-4 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition">
                                <i class="fas fa-redo mr-2"></i>Generate Again
                            </button>
                        </div>`;
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                console.error('Error processing content:', error);
                document.getElementById('processing-status').innerHTML = `
                    <div class="text-center py-4">
                        <div class="text-red-600 mb-2">
                            <i class="fas fa-exclamation-triangle text-2xl"></i>
                        </div>
                        <p class="text-red-600">Processing failed</p>
                        <p class="text-sm text-gray-500">${error.message}</p>
                        <button onclick="processContent()" class="mt-4 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition">
                            <i class="fas fa-retry mr-2"></i>Try Again
                        </button>
                    </div>`;
            }
        }

        function displayAudioResult(data) {
            const audioUrl = `/api/audio/${data.audio_filename}`;
            
            document.getElementById('audio-preview').innerHTML = `
                <div class="space-y-4">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                            <span class="font-semibold">Generated Audio</span>
                            <span class="text-sm text-gray-600">${data.provider_used} • ${data.duration.toFixed(1)}s</span>
                        </div>
                        <audio controls class="w-full">
                            <source src="${audioUrl}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="bg-blue-50 rounded p-3">
                            <div class="text-blue-600 font-semibold">Provider</div>
                            <div class="capitalize">${data.provider_used.replace('_', ' ')}</div>
                        </div>
                        <div class="bg-green-50 rounded p-3">
                            <div class="text-green-600 font-semibold">Quality</div>
                            <div>${Math.round(data.quality_score * 100)}%</div>
                        </div>
                    </div>
                    
                    ${data.metadata ? `
                        <div class="bg-gray-50 rounded p-3 text-sm">
                            <div class="font-semibold mb-2">Metadata:</div>
                            <div class="space-y-1 text-gray-600">
                                ${Object.entries(data.metadata).map(([key, value]) => 
                                    `<div><span class="font-medium">${key.replace('_', ' ')}:</span> ${value}</div>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>`;

            // Enable download button and video generation
            document.getElementById('download-options').innerHTML = `
                <a href="${audioUrl}" download class="w-full bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition text-center block">
                    <i class="fas fa-file-audio mr-2"></i>Download Audio (MP3)
                </a>
                <button disabled class="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-lg cursor-not-allowed">
                    <i class="fas fa-file-video mr-2"></i>Download Video (Not Generated Yet)
                </button>
                <button onclick="downloadScript()" class="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition">
                    <i class="fas fa-file-text mr-2"></i>Download Script (TXT)
                </button>`;
            
            // Show video generation option
            document.getElementById('video-preview').innerHTML = `
                <div class="space-y-4">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div class="font-semibold text-blue-800 mb-2">Ready for Video Generation!</div>
                        <p class="text-blue-700 text-sm mb-3">Choose your background style and generate your TikTok video.</p>
                        
                        <div class="space-y-3">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Background Style</label>
                                <select id="background-type" class="w-full p-2 border border-gray-300 rounded text-sm">
                                    <option value="geometric_patterns">Geometric Patterns (Clean & Modern)</option>
                                    <option value="minecraft_parkour">Minecraft Parkour (Gaming)</option>
                                    <option value="subway_surfers">Subway Surfers (Popular Choice)</option>
                                    <option value="satisfying_slime">Satisfying Slime (ASMR Style)</option>
                                    <option value="cooking_asmr">Cooking ASMR (Lifestyle)</option>
                                    <option value="nature_scenes">Nature Scenes (Calming)</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Video Format</label>
                                <select id="video-format" class="w-full p-2 border border-gray-300 rounded text-sm">
                                    <option value="tiktok">TikTok (9:16 Vertical)</option>
                                    <option value="instagram_reel">Instagram Reel (9:16 Vertical)</option>
                                    <option value="youtube_short">YouTube Short (9:16 Vertical)</option>
                                    <option value="square">Square (1:1 Instagram)</option>
                                </select>
                            </div>
                            
                            <button onclick="generateVideo('${data.audio_filename}')" class="w-full bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition font-semibold">
                                <i class="fas fa-video mr-2"></i>Generate Video (⚠️ Requires FFmpeg)
                            </button>
                        </div>
                    </div>
                </div>`;
                
            // Store current audio data for video generation
            window.currentAudioData = data;
        }

        async function generateVideo(audioFilename) {
            const content = document.getElementById('content-input').value;
            const backgroundType = document.getElementById('background-type').value;
            const videoFormat = document.getElementById('video-format').value;
            
            if (!content.trim()) {
                alert('Please enter some content first!');
                return;
            }

            // Show processing state
            document.getElementById('video-preview').innerHTML = `
                <div class="text-center py-8">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                    <p class="text-gray-600 font-semibold">Generating video...</p>
                    <p class="text-sm text-gray-500">This may take 1-3 minutes</p>
                    <div class="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3">
                        <p class="text-yellow-800 text-sm">
                            <i class="fas fa-info-circle mr-1"></i>
                            FFmpeg is required for video generation. Install with: <code>brew install ffmpeg</code>
                        </p>
                    </div>
                </div>`;

            try {
                const response = await fetch('/api/generate-video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: content,
                        audio_filename: audioFilename,
                        background_type: backgroundType,
                        video_format: videoFormat
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    displayVideoResult(result.data);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                console.error('Error generating video:', error);
                document.getElementById('video-preview').innerHTML = `
                    <div class="text-center py-8">
                        <div class="text-red-600 mb-4">
                            <i class="fas fa-exclamation-triangle text-4xl"></i>
                        </div>
                        <p class="text-red-600 font-semibold">Video generation failed</p>
                        <p class="text-sm text-gray-500 mb-4">${error.message}</p>
                        <div class="bg-red-50 border border-red-200 rounded p-3 mb-4">
                            <p class="text-red-800 text-sm">
                                <strong>Common issues:</strong><br>
                                • FFmpeg not installed: <code>brew install ffmpeg</code><br>
                                • Audio file not found<br>
                                • Insufficient disk space
                            </p>
                        </div>
                        <button onclick="generateVideo('${audioFilename}')" class="bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition">
                            <i class="fas fa-retry mr-2"></i>Try Again
                        </button>
                    </div>`;
            }
        }

        function displayVideoResult(data) {
            const videoUrl = `/api/video/${data.video_filename}`;
            
            document.getElementById('video-preview').innerHTML = `
                <div class="space-y-4">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                            <span class="font-semibold">Generated Video</span>
                            <span class="text-sm text-gray-600">${data.format} • ${data.duration.toFixed(1)}s</span>
                        </div>
                        <video controls class="w-full rounded-lg" style="max-height: 400px;">
                            <source src="${videoUrl}" type="video/mp4">
                            Your browser does not support the video element.
                        </video>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="bg-red-50 rounded p-3">
                            <div class="text-red-600 font-semibold">Format</div>
                            <div class="capitalize">${data.format.replace('_', ' ')}</div>
                        </div>
                        <div class="bg-purple-50 rounded p-3">
                            <div class="text-purple-600 font-semibold">File Size</div>
                            <div>${(data.file_size / (1024 * 1024)).toFixed(1)} MB</div>
                        </div>
                    </div>
                    
                    ${data.metadata ? `
                        <div class="bg-gray-50 rounded p-3 text-sm">
                            <div class="font-semibold mb-2">Video Details:</div>
                            <div class="space-y-1 text-gray-600">
                                <div><span class="font-medium">Resolution:</span> ${data.metadata.width}x${data.metadata.height}</div>
                                <div><span class="font-medium">FPS:</span> ${data.metadata.fps}</div>
                                <div><span class="font-medium">Video Codec:</span> ${data.metadata.video_codec}</div>
                                <div><span class="font-medium">Audio Codec:</span> ${data.metadata.audio_codec}</div>
                            </div>
                        </div>
                    ` : ''}
                </div>`;

            // Enable video download
            const downloadOptions = document.getElementById('download-options');
            const videoButton = downloadOptions.querySelector('button[disabled]');
            if (videoButton) {
                videoButton.outerHTML = `
                    <a href="${videoUrl}" download class="w-full bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition text-center block">
                        <i class="fas fa-file-video mr-2"></i>Download Video (MP4)
                    </a>`;
            }
        }

        function downloadScript() {
            const content = document.getElementById('content-input').value;
            if (!content.trim()) return;

            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'reddit_story_script.txt';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Reddit-to-TikTok Automation System Loaded');
            // You could add a startup check here
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/analyze", response_model=ProcessingResult)
async def analyze_content(request: ContentRequest):
    """Analyze Reddit content for quality and viral potential."""
    try:
        logger.info(f"Analyzing content ({len(request.text)} characters)")
        
        # Process content
        processed_content = content_processor.process(request.text, request.source_url)
        
        if processed_content is None:
            return ProcessingResult(
                success=False,
                message="Content analysis failed - content may not meet quality standards",
                data=None
            )
        
        # Convert to serializable format
        analysis_data = {
            "validation": {
                "is_valid": processed_content.validation.is_valid,
                "quality_score": processed_content.validation.quality_score,
                "word_count": processed_content.validation.word_count,
                "issues": processed_content.validation.issues,
                "recommendations": processed_content.validation.recommendations
            },
            "metadata": processed_content.metadata,
            "estimated_duration": processed_content.estimated_duration,
            "cleaned_text": processed_content.cleaned_text,
            "tts_optimized_text": processed_content.tts_optimized_text
        }
        
        return ProcessingResult(
            success=True,
            message="Content analyzed successfully",
            data=analysis_data
        )
        
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        return ProcessingResult(
            success=False,
            message=f"Analysis failed: {str(e)}",
            data=None
        )


@app.post("/api/synthesize", response_model=ProcessingResult)
async def synthesize_speech(request: TTSRequest):
    """Generate speech from text using the hybrid TTS system."""
    try:
        logger.info(f"Synthesizing speech with provider: {request.provider}")
        
        # First analyze content for optimal provider selection
        processed_content = content_processor.process(request.text)
        if processed_content is None:
            raise ValueError("Content processing failed")
        
        # Prepare content analysis for TTS selection
        content_analysis = {
            "quality_score": processed_content.validation.quality_score,
            "story_type": processed_content.metadata.get("story_type", "general"),
            "word_count": processed_content.validation.word_count,
            "emotional_score": 0.6,  # Would come from emotional analyzer
            "dominant_emotion": "neutral"
        }
        
        # Generate speech
        if request.provider and request.provider != "auto":
            # Force specific provider by modifying strategy
            strategy = tts_engine.get_strategy_for_content(content_analysis)
            from generators.tts_engine import TTSProvider
            provider_map = {
                "gtts": TTSProvider.GTTS,
                "edge_tts": TTSProvider.EDGE_TTS,
                "coqui": TTSProvider.COQUI,
                "pyttsx3": TTSProvider.PYTTSX3
            }
            if request.provider in provider_map:
                strategy.provider_priorities = [provider_map[request.provider]]
        
        # Create output directory
        output_dir = settings.get_output_path("audio")
        
        # Generate speech
        result = tts_engine.synthesize_with_fallback(
            processed_content.tts_optimized_text,
            content_analysis
        )
        
        if not result.success:
            raise ValueError(f"TTS synthesis failed: {result.error_message}")
        
        # Prepare response data
        response_data = {
            "provider_used": result.provider_used.value,
            "quality_score": result.quality_score,
            "duration": result.duration,
            "audio_filename": result.audio_path.name,
            "audio_path": str(result.audio_path),
            "metadata": result.metadata
        }
        
        return ProcessingResult(
            success=True,
            message="Speech synthesis completed successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        return ProcessingResult(
            success=False,
            message=f"Synthesis failed: {str(e)}",
            data=None
        )


@app.post("/api/generate-video", response_model=ProcessingResult)
async def generate_video(request: VideoRequest):
    """Generate video from text and audio."""
    try:
        logger.info(f"Generating video with background: {request.background_type}")
        
        # Find the audio file
        audio_path = None
        possible_paths = [
            settings.get_output_path("audio") / request.audio_filename,
            Path("/tmp/reddit_tiktok_tts") / request.audio_filename,
        ]
        
        # Search temp directories
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
        if temp_dir.exists():
            for audio_file in temp_dir.glob("*.mp3"):
                if audio_file.name == request.audio_filename:
                    possible_paths.append(audio_file)
        
        for path in possible_paths:
            if isinstance(path, Path) and path.exists():
                audio_path = path
                break
        
        if not audio_path:
            raise ValueError(f"Audio file not found: {request.audio_filename}")
        
        # Configure video generation
        background_map = {
            "geometric_patterns": BackgroundType.GEOMETRIC_PATTERNS,
            "minecraft_parkour": BackgroundType.MINECRAFT_PARKOUR,
            "subway_surfers": BackgroundType.SUBWAY_SURFERS,
            "satisfying_slime": BackgroundType.SATISFYING_SLIME,
            "cooking_asmr": BackgroundType.COOKING_ASMR,
            "nature_scenes": BackgroundType.NATURE_SCENES
        }
        
        format_map = {
            "tiktok": VideoFormat.TIKTOK,
            "instagram_reel": VideoFormat.INSTAGRAM_REEL,
            "youtube_short": VideoFormat.YOUTUBE_SHORT,
            "square": VideoFormat.SQUARE
        }
        
        config = VideoConfig(
            format=format_map.get(request.video_format, VideoFormat.TIKTOK),
            background_type=background_map.get(request.background_type, BackgroundType.GEOMETRIC_PATTERNS)
        )
        
        # Generate video
        result = video_generator.generate_video(
            audio_path=audio_path,
            text=request.text,
            config=config
        )
        
        if not result.success:
            raise ValueError(f"Video generation failed: {result.error_message}")
        
        # Prepare response data
        response_data = {
            "video_filename": result.video_path.name,
            "video_path": str(result.video_path),
            "duration": result.duration,
            "format": result.format.value,
            "file_size": result.file_size,
            "metadata": result.metadata
        }
        
        return ProcessingResult(
            success=True,
            message="Video generation completed successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        return ProcessingResult(
            success=False,
            message=f"Video generation failed: {str(e)}",
            data=None
        )


@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    try:
        # Look for audio file in temp directories
        possible_paths = [
            settings.get_output_path("audio") / filename,
            Path("/tmp/reddit_tiktok_tts") / filename,
            Path("/var/folders").glob(f"*/T/reddit_tiktok_tts/{filename}")
        ]
        
        for path in possible_paths:
            if isinstance(path, Path) and path.exists():
                return FileResponse(
                    path,
                    media_type="audio/mpeg",
                    filename=filename
                )
        
        # If not found in expected locations, search temp directories
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
        if temp_dir.exists():
            for audio_file in temp_dir.glob("*.mp3"):
                if audio_file.name == filename:
                    return FileResponse(
                        audio_file,
                        media_type="audio/mpeg", 
                        filename=filename
                    )
        
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving audio file")


@app.get("/api/video/{filename}")
async def serve_video(filename: str):
    """Serve generated video files."""
    try:
        # Look for video file in temp directories
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_videos"
        
        if temp_dir.exists():
            for video_file in temp_dir.glob("*.mp4"):
                if video_file.name == filename:
                    return FileResponse(
                        video_file,
                        media_type="video/mp4",
                        filename=filename
                    )
        
        raise HTTPException(status_code=404, detail="Video file not found")
        
    except Exception as e:
        logger.error(f"Error serving video file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving video file")


@app.get("/api/providers")
async def get_providers():
    """Get information about available TTS providers."""
    try:
        available_providers = tts_engine.tts_engine.get_available_providers()
        provider_info = tts_engine.tts_engine.get_provider_info()
        recommendations = tts_engine.get_recommended_setup()
        
        return {
            "available_providers": [p.value for p in available_providers],
            "provider_info": {p.value: info for p, info in provider_info.items()},
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error getting provider info: {e}")
        raise HTTPException(status_code=500, detail="Error getting provider information")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "tts_providers": len(tts_engine.tts_engine.get_available_providers())
    }


def run_web_app(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Run the web application."""
    logger.info(f"Starting Reddit-to-TikTok web interface at http://{host}:{port}")
    uvicorn.run(
        "src.web_app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_web_app()