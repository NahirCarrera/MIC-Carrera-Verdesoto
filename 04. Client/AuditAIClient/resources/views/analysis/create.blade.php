<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            {{ __('Nueva Auditoría de Calidad') }}
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6 text-gray-900">
                    
                    {{-- Mensajes de error --}}
                    @if($errors->any())
                        <div class="mb-4 p-4 bg-red-50 text-red-700 rounded border border-red-200">
                            <strong>⚠️ Atención:</strong> {{ $errors->first() }}
                        </div>
                    @endif

                    <form action="{{ route('audit.store') }}" method="POST" enctype="multipart/form-data" class="space-y-6">
                        @csrf
                        
                        {{-- Selector de Comida --}}
                        <div>
                            <label class="block font-medium text-sm text-gray-700 mb-2">Ingrediente a Auditar</label>
                            <select name="food_type" class="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                                
                                <option value="" disabled selected>-- Selecciona un ingrediente --</option>
                                
                                @foreach($foods as $food)
                                    {{-- 
                                        Value: We send the name (e.g., 'onion') because Python expects the string key.
                                        Label: We show the name capitalized and the threshold from DB.
                                    --}}
                                    <option value="{{ $food->name }}">
                                        {{ ucfirst($food->name) }} (Mínimo: {{ $food->min_threshold }}%)
                                    </option>
                                @endforeach

                            </select>
                        </div>

                        {{-- Subida de Imagen --}}
                        <div>
                            <label class="block font-medium text-sm text-gray-700 mb-2">Evidencia Fotográfica</label>
                            <input type="file" name="image" accept="image/*" class="block w-full text-sm text-gray-500
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-full file:border-0
                                file:text-sm file:font-semibold
                                file:bg-indigo-50 file:text-indigo-700
                                hover:file:bg-indigo-100" required>
                            <p class="mt-1 text-sm text-gray-500">Sube una foto clara de la bandeja.</p>
                        </div>

                        {{-- Botón --}}
                        <div class="flex justify-end">
                            <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded shadow transition">
                                Analizar Ahora
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</x-app-layout>