<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class Inspection extends Model
{
    protected $table = 'inspection';
    public $timestamps = false;

    protected $casts = [
        'created_at' => 'datetime', 
    ];

    public function video() {
        return $this->belongsTo(Video::class, 'video_id')->withDefault(); // withDefault evita errores si es null
    }

    public function category() {
        return $this->belongsTo(FoodCategory::class, 'category_id');
    }

    public function status() {
        return $this->belongsTo(InspectionStatus::class, 'status_id');
    }

    // Nueva relación para saber quién subió la foto
    public function user() {
        return $this->belongsTo(User::class, 'user_id_validator');
    }
}