import { randomUUID } from "node:crypto";
import { S3Client, PutObjectCommand, ListObjectsV2Command, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const allowedTypes = new Set(["image/png", "image/jpeg", "image/webp", "image/avif"]);
const maxImageBytes = 12 * 1024 * 1024;
const collectionContext = `CELVANI HOUSE CODE: premium accessible luxury; minimalist luxury identity; protect the established CELVANI logo and brand equity; product quality and authenticity outrank hype. COLLECTION 001 CONTINUITY: oversized hoodies in black, brown, green, navy and red; fitted upper denim with a dramatic flare below the knee in multiple washes; cropped black puffer; black/cream logo knit; black/cream long sleeve. Preserve silhouettes and details from supplied references unless the user explicitly asks to change them. Do not invent or substitute another brand's logo. Do not add arbitrary text, watermarks, or third-party branding. Treat uploaded references as authoritative visual direction.`;

function getStorage() {
  const required = ["ASSETS_S3_ENDPOINT","ASSETS_S3_BUCKET","ASSETS_S3_REGION","ASSETS_S3_ACCESS_KEY_ID","ASSETS_S3_SECRET_ACCESS_KEY"];
  if (required.some(key => !process.env[key])) return null;
  return new S3Client({
    region: process.env.ASSETS_S3_REGION,
    endpoint: process.env.ASSETS_S3_ENDPOINT,
    forcePathStyle: false,
    credentials: { accessKeyId: process.env.ASSETS_S3_ACCESS_KEY_ID, secretAccessKey: process.env.ASSETS_S3_SECRET_ACCESS_KEY }
  });
}
function safeName(value) {
  return String(value || "reference-image").normalize("NFKD").replace(/[^a-zA-Z0-9._-]+/g,"-").replace(/^-+|-+$/g,"").slice(0,100) || "reference-image";
}
async function signedAsset(s3, key, name, mimeType) {
  const url = await getSignedUrl(s3, new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}), {expiresIn:3600});
  return {key,name,mimeType,url};
}
async function bodyToBuffer(body) {
  if (body?.transformToByteArray) return Buffer.from(await body.transformToByteArray());
  const chunks=[]; for await (const chunk of body) chunks.push(Buffer.from(chunk)); return Buffer.concat(chunks);
}
export function registerCreativeRoutes(app,{requireAgentToken}) {
  app.get("/api/orni/creative/status",requireAgentToken,(_req,res)=>{
    const storage=getStorage();
    const provider=process.env.IMAGE_PROVIDER||"cloudflare";
    const keyReady=provider==="cloudflare"?Boolean(process.env.CLOUDFLARE_WORKER_URL&&process.env.ORNI_WORKER_TOKEN):provider==="fal"?Boolean(process.env.FAL_KEY):Boolean(process.env.OPENAI_API_KEY);
    res.json({ok:Boolean(storage&&keyReady),provider,imageModel:provider==="cloudflare"?"black-forest-labs/flux-3-image-klein":provider==="fal"?"FLUX.2 Pro":"gpt-image-2.6-sunburst",videoModels:provider==="cloudflare"?["klingai/kling-v4-flash","minimax/h3-highspeed"]:[],storage:storage?"connected":"not_configured",generation:keyReady});
  });
  app.get("/api/orni/assets",requireAgentToken,async(_req,res)=>{
    const s3=getStorage(); if(!s3)return res.status(503).json({error:"CELVANI asset storage is not configured."});
    try{
      const listed=await s3.send(new ListObjectsV2Command({Bucket:process.env.ASSETS_S3_BUCKET,Prefix:"celvani/"}));
      const assets=await Promise.all((listed.Contents||[]).filter(x=>x.Key&&x.Size>0).sort((a,b)=>(b.LastModified?.getTime()||0)-(a.LastModified?.getTime()||0)).slice(0,100).map(async item=>{
        const key=item.Key; const name=decodeURIComponent(key.split("/").pop().replace(/^\d+-[a-f0-9-]+-/,""));
        const mimeType=key.endsWith(".jpg")||key.endsWith(".jpeg")?"image/jpeg":key.endsWith(".webp")?"image/webp":key.endsWith(".avif")?"image/avif":"image/png";
        return {...await signedAsset(s3,key,name,mimeType),createdAt:item.LastModified?.toISOString()||null};
      }));
      return res.json({assets});
    }catch(error){console.error("ORNI asset listing failed",{name:error?.name});return res.status(502).json({error:"Could not load the CELVANI reference library."});}
  });
  app.post("/api/orni/assets",requireAgentToken,async(req,res)=>{
    const s3=getStorage(); if(!s3)return res.status(503).json({error:"CELVANI asset storage is not configured."});
    const {name,mimeType,data}=req.body||{};
    if(!allowedTypes.has(mimeType)||typeof data!=="string")return res.status(400).json({error:"Upload a PNG, JPEG, WEBP, or AVIF image."});
    const buffer=Buffer.from(data,"base64");
    if(!buffer.length||buffer.length>maxImageBytes)return res.status(413).json({error:"Images must be smaller than 12 MB."});
    const filename=safeName(name); const key="celvani/"+Date.now()+"-"+randomUUID()+"-"+filename;
    try{
      await s3.send(new PutObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key,Body:buffer,ContentType:mimeType,Metadata:{originalname:encodeURIComponent(filename)}}));
      const asset=await signedAsset(s3,key,filename,mimeType);
      return res.status(201).json({asset});
    }catch(error){console.error("ORNI asset upload failed",{name:error?.name});return res.status(502).json({error:"Could not save this image to the CELVANI library."});}
  });
  app.post("/api/orni/designs/generate",requireAgentToken,async(req,res)=>{
    const provider=process.env.IMAGE_PROVIDER||"cloudflare";
    const apiKey=provider==="fal"?process.env.FAL_KEY:process.env.OPENAI_API_KEY;
    const workerReady=Boolean(process.env.CLOUDFLARE_WORKER_URL&&process.env.ORNI_WORKER_TOKEN);
    if(provider==="cloudflare"&&!workerReady)return res.status(503).json({error:"Configure CLOUDFLARE_WORKER_URL and ORNI_WORKER_TOKEN on the ORNI API Railway service."});
    if(provider!=="cloudflare"&&!apiKey)return res.status(503).json({error:provider==="fal"?"Add FAL_KEY to the ORNI API Railway service to enable image generation.":"OpenAI image generation is not configured on ORNI."});
    const s3=getStorage(); if(!s3)return res.status(503).json({error:"CELVANI asset storage is not configured."});
    const prompt=typeof req.body?.prompt==="string"?req.body.prompt.trim():"";
    const assetKeys=Array.isArray(req.body?.assetKeys)?req.body.assetKeys.filter(x=>typeof x==="string"&&x.startsWith("celvani/")).slice(0,4):[];
    if(!prompt||prompt.length>6000)return res.status(400).json({error:"Write a design brief between 1 and 6000 characters."});
    try{
      const fullPrompt=collectionContext+"\\n\\nUSER DESIGN BRIEF:\\n"+prompt;
      let imageBuffer,model,contentType="image/png";
      if(provider==="cloudflare"){
        const imageUrls=[];
        for(const key of assetKeys){
          const obj=await s3.send(new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}));
          imageUrls.push((await signedAsset(s3,key,key.split("/").pop(),obj.ContentType||"image/png")).url);
        }
        const workerUrl=process.env.CLOUDFLARE_WORKER_URL.replace(/\\/+$/,"");
        const response=await fetch(workerUrl+"/image",{method:"POST",headers:{"Authorization":"Bearer "+process.env.ORNI_WORKER_TOKEN,"Content-Type":"application/json"},body:JSON.stringify({prompt:fullPrompt,images:imageUrls,resolution:"1k"}),signal:AbortSignal.timeout(240000)});
        const result=await response.json().catch(()=>({}));
        if(!response.ok||!result.output?.url)return res.status(response.status===429?429:502).json({error:result.error||"Cloudflare FLUX image generation failed.",provider:"cloudflare"});
        const imageResponse=await fetch(result.output.url,{signal:AbortSignal.timeout(60000)});
        if(!imageResponse.ok)return res.status(502).json({error:"Could not retrieve the generated image from Cloudflare FLUX."});
        imageBuffer=Buffer.from(await imageResponse.arrayBuffer());
        contentType=imageResponse.headers.get("content-type")||"image/png";
        model=result.model||"black-forest-labs/flux-3-image-klein";
      }else if(provider==="fal"){
        const imageUrls=[];
        for(const key of assetKeys){
          const obj=await s3.send(new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}));
          const bytes=await bodyToBuffer(obj.Body);
          if(bytes.length>maxImageBytes)continue;
          imageUrls.push("data:"+(obj.ContentType||"image/png")+";base64,"+bytes.toString("base64"));
        }
        const endpoint=imageUrls.length?"https://fal.run/fal-ai/flux-2-pro/edit":"https://fal.run/fal-ai/flux-2-pro";
        const input=imageUrls.length?{prompt:fullPrompt,image_urls:imageUrls,image_size:"square_hd",output_format:"png"}:{prompt:fullPrompt,image_size:"square_hd",output_format:"png"};
        const response=await fetch(endpoint,{method:"POST",headers:{"Authorization":"Key "+apiKey,"Content-Type":"application/json"},body:JSON.stringify(input),signal:AbortSignal.timeout(180000)});
        const result=await response.json().catch(()=>({}));
        if(!response.ok){
          const message=result?.detail?.[0]?.msg||result?.detail||result?.error||"FLUX image generation request failed.";
          console.error("ORNI fal image provider error",{status:response.status});
          return res.status(response.status===429?429:502).json({error:typeof message==="string"?message:"FLUX provider rejected the request.",provider:"fal",providerStatus:response.status});
        }
        const output=result.images?.[0];
        if(!output?.url)return res.status(502).json({error:"FLUX returned no completed image. Try a shorter brief or fewer references."});
        const imageResponse=await fetch(output.url,{signal:AbortSignal.timeout(60000)});
        if(!imageResponse.ok)return res.status(502).json({error:"Could not retrieve the generated image from FLUX."});
        imageBuffer=Buffer.from(await imageResponse.arrayBuffer());
        contentType=output.content_type||imageResponse.headers.get("content-type")||"image/png";
        model=imageUrls.length?"fal-ai/flux-2-pro/edit":"fal-ai/flux-2-pro";
      }else{
        const content=[{type:"input_text",text:fullPrompt}];
        for(const key of assetKeys){
          const obj=await s3.send(new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}));
          const bytes=await bodyToBuffer(obj.Body);
          if(bytes.length<=maxImageBytes)content.push({type:"input_image",image_url:"data:"+(obj.ContentType||"image/png")+";base64,"+bytes.toString("base64")});
        }
        const payload={model:"gpt-5.5",tools:[{type:"image_generation",model:"gpt-image-2.6-sunburst",action:assetKeys.length?"auto":"generate"}],input:[{role:"user",content}]};
        const response=await fetch("https://api.openai.com/v1/responses",{method:"POST",headers:{"Authorization":"Bearer "+apiKey,"Content-Type":"application/json"},body:JSON.stringify(payload),signal:AbortSignal.timeout(120000)});
        const result=await response.json().catch(()=>({}));
        if(!response.ok)return res.status(response.status===429?429:502).json({error:result?.error?.message||"Image generation provider request failed.",provider:"openai"});
        const call=(result.output||[]).find(item=>item.type==="image_generation_call"&&item.result);
        if(!call?.result)return res.status(502).json({error:"The image model returned no completed image."});
        imageBuffer=Buffer.from(call.result,"base64");model="gpt-image-2.6-sunburst";contentType="image/png";
      }
      const extension=contentType.includes("jpeg")?"jpg":contentType.includes("webp")?"webp":"png";
      const key="celvani/generated-"+Date.now()+"-"+randomUUID()+"."+extension;
      await s3.send(new PutObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key,Body:imageBuffer,ContentType:contentType,Metadata:{originalname:"ORNI-generated-design."+extension}}));
      const asset=await signedAsset(s3,key,"ORNI generated design",contentType);
      return res.json({ok:true,provider,model,asset,generatedAt:new Date().toISOString()});
    }catch(error){
      const timedOut=error?.name==="TimeoutError"||error?.name==="AbortError";
      console.error("ORNI creative generation failed",{name:error?.name,timedOut});
      return res.status(timedOut?504:502).json({error:timedOut?"Image generation timed out.":"Could not complete the CELVANI image generation request.",provider});
    }
  });

  app.post("/api/orni/videos/generate",requireAgentToken,async(req,res)=>{
    const workerUrl=process.env.CLOUDFLARE_WORKER_URL?.replace(/\\/+$/,"");
    const workerToken=process.env.ORNI_WORKER_TOKEN;
    const s3=getStorage();
    if(!workerUrl||!workerToken)return res.status(503).json({error:"Configure CLOUDFLARE_WORKER_URL and ORNI_WORKER_TOKEN on the ORNI API Railway service."});
    if(!s3)return res.status(503).json({error:"CELVANI asset storage is not configured."});
    const prompt=typeof req.body?.prompt==="string"?req.body.prompt.trim():"";
    const model=req.body?.model==="minimax"?"minimax":"kling";
    const duration=Number(req.body?.duration??5);
    if(!prompt||prompt.length>26000)return res.status(400).json({error:"Write a video brief between 1 and 26000 characters."});
    const assetKeys=Array.isArray(req.body?.assetKeys)?req.body.assetKeys.filter(x=>typeof x==="string"&&x.startsWith("celvani/")).slice(0,4):[];
    try{
      const referenceImages=[];
      for(const key of assetKeys){
        const obj=await s3.send(new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}));
        referenceImages.push((await signedAsset(s3,key,key.split("/").pop(),obj.ContentType||"image/png")).url);
      }
      const response=await fetch(workerUrl+"/video",{method:"POST",headers:{"Authorization":"Bearer "+workerToken,"Content-Type":"application/json"},body:JSON.stringify({prompt,model,duration,aspect_ratio:req.body?.aspect_ratio||"9:16",reference_images:referenceImages}),signal:AbortSignal.timeout(300000)});
      const result=await response.json().catch(()=>({}));
      if(!response.ok||!result.output?.url)return res.status(response.status===429?429:502).json({error:result.error||"Cloudflare video generation failed.",provider:"cloudflare",model});
      const videoResponse=await fetch(result.output.url,{signal:AbortSignal.timeout(120000)});
      if(!videoResponse.ok)return res.status(502).json({error:"Could not retrieve the generated video from Cloudflare."});
      const videoBuffer=Buffer.from(await videoResponse.arrayBuffer());
      const key="celvani/generated-video-"+Date.now()+"-"+randomUUID()+".mp4";
      await s3.send(new PutObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key,Body:videoBuffer,ContentType:"video/mp4",Metadata:{originalname:"ORNI-generated-video.mp4"}}));
      const asset=await signedAsset(s3,key,"ORNI generated video","video/mp4");
      return res.json({ok:true,provider:"cloudflare",model:result.model||model,asset,generatedAt:new Date().toISOString()});
    }catch(error){
      const timedOut=error?.name==="TimeoutError"||error?.name==="AbortError";
      console.error("ORNI video generation failed",{name:error?.name,timedOut});
      return res.status(timedOut?504:502).json({error:timedOut?"Video generation timed out.":"Could not complete the CELVANI video generation request.",provider:"cloudflare"});
    }
  });
}
