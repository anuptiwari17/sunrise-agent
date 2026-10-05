/**
 * API configuration.
 * When deployed on Vercel, set VITE_API_URL in Vercel's Environment Variables
 * to your Render backend URL (e.g. https://sunrise-agent.onrender.com).
 * In local development, leave it empty to use Vite's proxy.
 */
export const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
