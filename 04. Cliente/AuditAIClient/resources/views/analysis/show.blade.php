<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            Resultados del Análisis
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-5xl mx-auto sm:px-6 lg:px-8">
            
            {{-- Tarjeta de Estatus Principal --}}
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg mb-6 text-center p-8">
                <h3 class="text-lg font-medium text-gray-500 uppercase tracking-wider">Diagnóstico</h3>
                
                @if($data['is_incident'])
                    <div class="mt-4 inline-flex items-center px-6 py-3 rounded-full bg-red-100 text-red-800 border-2 border-red-200">
                        <svg class="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        <span class="text-3xl font-bold">INCIDENTE DETECTADO</span>
                    </div>
                    <p class="mt-4 text-red-600 font-medium">La bandeja está vacía o por debajo del nivel mínimo.</p>
                @else
                    <div class="mt-4 inline-flex items-center px-6 py-3 rounded-full bg-green-100 text-green-800 border-2 border-green-200">
                        <svg class="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        <span class="text-3xl font-bold">ESTADO NORMAL</span>
                    </div>
                    <p class="mt-4 text-green-600 font-medium">Nivel de comida adecuado para operar.</p>
                @endif
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                {{-- Columna Izquierda: Imagen --}}
                <div class="bg-white p-4 shadow-sm rounded-lg">
                    <h4 class="font-bold text-gray-700 mb-3 border-b pb-2">Evidencia Analizada</h4>
                    <div class="rounded-lg overflow-hidden border border-gray-200">
                        <img src="{{ asset($imageUrl) }}" alt="Evidencia" class="w-full h-auto object-cover">
                    </div>
                </div>

                {{-- Columna Derecha: Datos Técnicos --}}
                <div class="bg-white p-6 shadow-sm rounded-lg">
                    <h4 class="font-bold text-gray-700 mb-4 border-b pb-2">Métricas Técnicas</h4>
                    
                    <dl class="space-y-4">
                        <div class="flex justify-between items-center">
                            <dt class="text-gray-500">Ingrediente</dt>
                            <dd class="font-mono font-bold text-lg capitalize">{{ $data['food_type'] }}</dd>
                        </div>
                        
                        <div class="flex justify-between items-center bg-gray-50 p-3 rounded">
                            <dt class="text-gray-700 font-medium">Llenado Detectado</dt>
                            <dd class="font-bold text-2xl {{ $data['is_incident'] ? 'text-red-600' : 'text-blue-600' }}">
                                {{ $data['percentage'] }}%
                            </dd>
                        </div>

                        <div class="flex justify-between items-center text-sm">
                            <dt class="text-gray-400">Umbral Mínimo Requerido</dt>
                            <dd class="text-gray-600 font-mono">{{ $data['min_threshold'] }}%</dd>
                        </div>
                    </dl>

                    <div class="mt-8 pt-6 border-t">
                        <a href="{{ route('audit.create') }}" class="block w-full text-center bg-gray-800 hover:bg-gray-700 text-white font-bold py-3 rounded transition">
                            Auditar Otra Bandeja
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</x-app-layout>