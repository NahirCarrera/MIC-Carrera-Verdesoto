<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use App\Models\FoodCategory;
// Agregamos el Facade Auth por si prefieres usar Auth::id()
use Illuminate\Support\Facades\Auth; 

class AnalysisController extends Controller
{
    // Show the upload form
    public function create()
    {
        $foods = FoodCategory::orderBy('name', 'asc')->get();
        return view('analysis.create', compact('foods'));
    }

    // Process the image and call Python API
    public function store(Request $request)
    {
        // 1. Validation
        $request->validate([
            'image' => 'required|image|mimes:jpeg,png,jpg|max:5120',
            'food_type' => 'required|string|exists:food_category,name',
        ]);

        // 2. Store image locally (public disk)
        $path = $request->file('image')->store('audits', 'public');
        $imageUrl = Storage::url($path);

        // 3. Prepare file for API
        $absolutePath = storage_path("app/public/{$path}");
        $fileStream = fopen($absolutePath, 'r');

       try {
            /** @var \Illuminate\Http\Client\Response $response */
            $response = Http::attach(
                'file', $fileStream, 'evidence.jpg'
            )->post('http://127.0.0.1:8000/analyze-food', [
                'type' => $request->food_type,
                // Opción A (Más limpia usando Request):
                'user_id' => $request->user()->id, 
                
                // --- NUEVO: Enviamos la ruta real de la imagen ---
                'image_url' => $imageUrl
            ]);

            // Close stream
            if (is_resource($fileStream)) fclose($fileStream);

            if ($response->failed()) {
                return back()->withErrors(['api' => 'Error de conexión con IA: ' . $response->body()]);
            }

            $data = $response->json();

        } catch (\Exception $e) {
            // Cerramos el stream por si falló antes de llegar al fclose de arriba
            if (isset($fileStream) && is_resource($fileStream)) fclose($fileStream);
            
            return back()->withErrors(['api' => 'El servidor de IA no responde. Verifica que esté encendido.']);
        }

        // 5. Return result view
        return view('analysis.show', [
            'imageUrl' => $imageUrl,
            'data' => $data
        ]);
    }

    public function history(Request $request)
    {
        $query = \App\Models\Inspection::with(['user', 'category', 'status']);

        if ($request->filled('start_date')) {
            $query->whereDate('created_at', '>=', $request->start_date);
        }

        if ($request->filled('end_date')) {
            $query->whereDate('created_at', '<=', $request->end_date);
        }

        $inspections = $query->orderByDesc('created_at')->paginate(10);

        return view('analysis.history', compact('inspections'));
    }
}