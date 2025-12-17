<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            {{ __('Panel de Control') }}
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {{-- TARJETA 1: NUEVA AUDITORÍA (Solo Imágenes) --}}
                <a href="{{ route('audit.create') }}" class="block group">
                    <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg hover:shadow-lg transition-shadow duration-300 h-full border-l-4 border-indigo-500">
                        <div class="p-8 flex items-center">
                            <div class="p-4 bg-indigo-100 rounded-full text-indigo-600 mr-6 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                            </div>
                            <div>
                                <h3 class="text-2xl font-bold text-gray-800 group-hover:text-indigo-600 transition-colors">Nueva Auditoría</h3>
                                <p class="mt-2 text-gray-600">Subir una foto de la bandeja para análisis de llenado.</p>
                            </div>
                        </div>
                    </div>
                </a>

                {{-- TARJETA 2: HISTORIAL Y FILTROS --}}
                <a href="{{ route('audit.history') }}" class="block group">
                    <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg hover:shadow-lg transition-shadow duration-300 h-full border-l-4 border-green-500">
                        <div class="p-8 flex items-center">
                            <div class="p-4 bg-green-100 rounded-full text-green-600 mr-6 group-hover:bg-green-600 group-hover:text-white transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                </svg>
                            </div>
                            <div>
                                <h3 class="text-2xl font-bold text-gray-800 group-hover:text-green-600 transition-colors">Historial de Auditorías</h3>
                                <p class="mt-2 text-gray-600">Ver todas las inspecciones.</p>
                            </div>
                        </div>
                    </div>
                </a>

            </div>
        </div>
    </div>
</x-app-layout>