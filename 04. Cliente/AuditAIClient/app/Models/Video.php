<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class Video extends Model
{
    protected $table = 'video'; // Nombre exacto en Postgres
    public $timestamps = false; // Python no usa created_at/updated_at de Laravel

    protected $casts = [
        'date' => 'datetime', // Para poder filtrar por fecha fácilmente
    ];
}