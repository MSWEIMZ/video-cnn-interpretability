# Visual Semantic Knowledge Discovery for Multimodal Intent Recognition

**authors**: Yaoyang Cheng

**year**: 2025 | **label**: core | **score**: 4.1

**arXiv**: [fe4effd689bfad626dd6d5ecf2f7df61087abb4f](https://www.semanticscholar.org/paper/fe4effd689bfad626dd6d5ecf2f7df61087abb4f)

**query**: core | spatiotemporal convolution video understanding

---

## abstract

Multimodal intent recognition is vital for understanding human interactions across diverse real-world scenarios, leveraging various modalities to discern user intents. However, current approaches predominantly prioritize text, overlooking rich semantic cues in video modalities, such as body language and expressions, which are closely linked to intent and can be more easily integrated with both text and audio semantics. This paper introduces ViSK, a Visual Semantic Knowledge Discovery model using adaptive perturbation and gradient-based quantification. First, we employ Video Swin Transformer as the backbone to extract feature maps from video frames in the form of spatiotemporal blocks which are considered as the elementary units of visual semantics. Then, we employ an adaptive perturbation module to generate instance-aware noises by transforming input features into perturbation parameters through stacked convolution layers. The noises are applied to obtain perturbed features after scaling. Finally, on the basis of high-quality perturbed features, we introduce a quantification mechanism by estimating gradients based on the DNN’s Lipschitz condition to evaluate the contribution of each spatiotemporal block for intent recognition. The original features are then weighted by the quantification score to achieve visual semantic knowledge features for video-based intent recognition. To assess the effectiveness of discovered visual semantics in enhancing multimodal fusion, we also construct a multimodal intent recognition framework to refine and leverage semantic features. Extensive experiments across two challenging datasets demonstrate that our approach significantly outperforms state-of-the-art methods. Visualization results provide deeper insights into discovered semantics and serve as a pioneering work for interpretability research in multimodal intent recognition (The full data and codes are available at https://drive.google.com/file/d/1eUpYVg9-k0fopCWsNyRRGk0_2XZyIRoc/view?usp=sharing).

---

*generated at 2026-06-27 05:06*
