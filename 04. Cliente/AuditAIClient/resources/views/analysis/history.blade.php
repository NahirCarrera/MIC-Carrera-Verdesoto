<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            {{ __('Historial de Auditorías') }}
        </h2>
    </x-slot>

    {{-- 1. AGREGAMOS x-data AQUÍ PARA CONTROLAR EL MODAL --}}
    <div class="py-12" x-data="{ showModal: false, imgUrl: '' }">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            
            {{-- SECCIÓN DE FILTROS (Igual que antes) --}}
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg mb-6 p-6">
                <form method="GET" action="{{ route('audit.history') }}" class="flex flex-col md:flex-row gap-4 items-end">
                    
                    {{-- Filtro Fecha Inicio --}}
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Desde</label>
                        <input type="date" name="start_date" value="{{ request('start_date') }}" 
                               class="border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 w-full">
                    </div>

                    {{-- Filtro Fecha Fin --}}
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
                        <input type="date" name="end_date" value="{{ request('end_date') }}" 
                               class="border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 w-full">
                    </div>

                    {{-- Botones --}}
                    <div class="flex gap-2">
                        <button type="submit" class="bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded shadow transition">
                            Filtrar
                        </button>
                        
                        @if(request('start_date') || request('end_date'))
                            <a href="{{ route('audit.history') }}" class="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 font-bold py-2 px-4 rounded shadow transition">
                                Limpiar
                            </a>
                        @endif
                    </div>
                </form>
            </div>

            {{-- TABLA DE RESULTADOS --}}
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6 text-gray-900 overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha y Hora</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Auditor</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ingrediente</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nivel</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evidencia</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            @forelse($inspections as $inspection)
                                <tr class="hover:bg-gray-50 transition">
                                    {{-- Columna Fecha --}}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        @if($inspection->created_at)
                                            {{ \Carbon\Carbon::parse($inspection->created_at)->format('d/m/Y H:i') }}
                                        @else
                                            <span class="text-gray-400 italic">Sin fecha</span>
                                        @endif
                                    </td>

                                    {{-- Columna Auditor --}}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                                        <div class="flex items-center">
                                            <div class="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 mr-2 font-bold text-xs">
                                                {{ substr($inspection->user->name ?? 'S', 0, 1) }}
                                            </div>
                                            {{ $inspection->user->name ?? 'Sistema' }}
                                        </div>
                                    </td>

                                    {{-- Columna Ingrediente --}}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 capitalize">
                                        {{ $inspection->category->name ?? 'Desconocido' }}
                                    </td>

                                    {{-- Columna Porcentaje --}}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-bold">
                                        {{ $inspection->percentage }}%
                                    </td>

                                    {{-- Columna Estado --}}
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        @if($inspection->status && $inspection->status->is_anomaly)
                                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800 border border-red-200">
                                                INCIDENTE
                                            </span>
                                        @else
                                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 border border-green-200">
                                                NORMAL
                                            </span>
                                        @endif
                                    </td>

                                    {{-- Columna Evidencia (MODIFICADA) --}}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        {{-- 2. CAMBIAMOS EL <A> POR UN <BUTTON> QUE ACTIVA ALPINE --}}
                                        <button 
                                            @click="imgUrl = '{{ asset($inspection->screenshot_url) }}'; showModal = true"
                                            class="text-indigo-600 hover:text-indigo-900 flex items-center focus:outline-none"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                            Ver Foto
                                        </button>
                                    </td>
                                </tr>
                            @empty
                                <tr>
                                    <td colspan="6" class="px-6 py-10 text-center text-gray-500">
                                        <div class="flex flex-col items-center justify-center">
                                            <svg class="h-12 w-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                            </svg>
                                            <p class="text-lg font-medium">No se encontraron auditorías</p>
                                            <p class="text-sm">Intenta ajustar los filtros de fecha o crea una nueva auditoría.</p>
                                        </div>
                                    </td>
                                </tr>
                            @endforelse
                        </tbody>
                    </table>
                    
                    {{-- Paginación --}}
                    <div class="mt-4">
                        {{ $inspections->links() }}
                    </div>
                </div>
            </div>
        </div>

        {{-- 3. EL MODAL (VENTANA FLOTANTE) --}}
        <div x-show="showModal" 
             style="display: none;"
             class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm p-4 transition-opacity"
             x-transition:enter="transition ease-out duration-300"
             x-transition:enter-start="opacity-0"
             x-transition:enter-end="opacity-100"
             x-transition:leave="transition ease-in duration-200"
             x-transition:leave-start="opacity-100"
             x-transition:leave-end="opacity-0">
            
            <div @click.away="showModal = false" class="relative max-w-4xl w-full bg-white rounded-lg shadow-2xl overflow-hidden">
                
                <button @click="showModal = false" class="absolute top-2 right-2 text-gray-500 hover:text-gray-800 bg-white rounded-full p-1 focus:outline-none z-10">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>

                <div class="flex justify-center items-center bg-gray-100">
                    <img :src="imgUrl" alt="Evidencia Auditoría" class="max-h-[80vh] w-auto object-contain">
                </div>
            </div>
        </div>

    </div>
</x-app-layout>