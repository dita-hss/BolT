#!/bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=00:05:00
#SBATCH --partition=amilan
#SBATCH -c 16
#SBATCH --output=prep_hcp-%j.out
#SBATCH --account=ucb474_asc1

module purge

module load anaconda 
conda activate BolT

cd /projects/alar6830/BolT

python prep.py --dataset hcpMotor --atlas brodmann --name fNIRS --fnirs True -u False

echo "done prepping"
