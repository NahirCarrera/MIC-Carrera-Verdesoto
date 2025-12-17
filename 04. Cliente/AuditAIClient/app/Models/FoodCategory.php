<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class FoodCategory extends Model
{
    use HasFactory;

    // 1. Define explicit table name (created by Python/SQL)
    protected $table = 'food_category';

    // 2. Disable timestamps (since the table doesn't have created_at/updated_at)
    public $timestamps = false;

    // 3. Allow mass assignment (optional, for reading mostly)
    protected $fillable = [
        'name',
        'algorithm',
        'min_threshold'
    ];
}