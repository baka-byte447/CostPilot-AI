import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { runOptimizer } from "../services/api"

export default function ScalingPanel() {

  const scale = async () => {
    const res = await runOptimizer()
    alert(`Scaled to ${res.data.new_replicas} replicas`)
  }

  return (

    <motion.div whileHover={{ scale: 1.05 }}>

      <Button
        className="bg-accent text-black text-lg px-6 py-4"
        onClick={scale}
      >
        Run AI Optimizer
      </Button>

    </motion.div>
  )
}


