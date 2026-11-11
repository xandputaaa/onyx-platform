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
    forcePathStyle: true,
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
    res.json({ok:Boolean(storage&&process.env.OPENAI_API_KEY),provider:"openai",imageModel:"gpt-image-2.6-sunburst",storage:storage?"connected":"not_configured",generation:Boolean(process.env.OPENAI_API_KEY)});
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
    if(!process.env.OPENAI_API_KEY)return res.status(503).json({error:"OpenAI image generation is not configured on ORNI."});
    const s3=getStorage(); if(!s3)return res.status(503).json({error:"CELVANI asset storage is not configured."});
    const prompt=typeof req.body?.prompt==="string"?req.body.prompt.trim():"";
    const assetKeys=Array.isArray(req.body?.assetKeys)?req.body.assetKeys.filter(x=>typeof x==="string"&&x.startsWith("celvani/")).slice(0,4):[];
    const previousResponseId=typeof req.body?.previousResponseId==="string"?req.body.previousResponseId:null;
    if(!prompt||prompt.length>6000)return res.status(400).json({error:"Write a design brief between 1 and 6000 characters."});
    try{
      const content=[{type:"input_text",text:collectionContext+"\n\nUSER DESIGN BRIEF:\n"+prompt}];
      if(!previousResponseId){
        for(const key of assetKeys){
          const obj=await s3.send(new GetObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key}));
          const bytes=await bodyToBuffer(obj.Body);
          if(bytes.length>maxImageBytes)continue;
          const mime=obj.ContentType||"image/png";
          content.push({type:"input_image",image_url:"data:"+mime+";base64,"+bytes.toString("base64")});
        }
      }
      const payload={model:"gpt-5.5",tools:[{type:"image_generation",model:"gpt-image-2.6-sunburst",action:(assetKeys.length||previousResponseId)?"auto":"generate"}],input:[{role:"user",content}]};
      if(previousResponseId)payload.previous_response_id=previousResponseId;
      const response=await fetch("https://api.openai.com/v1/responses",{method:"POST",headers:{"Authorization":"Bearer "+process.env.OPENAI_API_KEY,"Content-Type":"application/json"},body:JSON.stringify(payload),signal:AbortSignal.timeout(120000)});
      const result=await response.json().catch(()=>({}));
      if(!response.ok){const message=result?.error?.message||"Image generation provider request failed.";console.error("ORNI image provider error",{status:response.status,code:result?.error?.code});return res.status(response.status===429?429:502).json({error:message,provider:"openai",providerStatus:response.status});}
      const call=(result.output||[]).find(item=>item.type==="image_generation_call"&&item.result);
      if(!call?.result)return res.status(502).json({error:"The image model returned no completed image. Try a shorter brief or fewer references."});
      const imageBuffer=Buffer.from(call.result,"base64");
      const key="celvani/generated-"+Date.now()+"-"+randomUUID()+".png";
      await s3.send(new PutObjectCommand({Bucket:process.env.ASSETS_S3_BUCKET,Key:key,Body:imageBuffer,ContentType:"image/png",Metadata:{originalname:"ORNI-generated-design.png"}}));
      const asset=await signedAsset(s3,key,"ORNI generated design","image/png");
      return res.json({ok:true,provider:"openai",model:"gpt-image-2.6-sunburst",responseId:result.id||null,asset,generatedAt:new Date().toISOString()});
    }catch(error){
      const timedOut=error?.name==="TimeoutError"||error?.name==="AbortError";
      console.error("ORNI creative generation failed",{name:error?.name,timedOut});
      return res.status(timedOut?504:502).json({error:timedOut?"Image generation timed out.":"Could not complete the CELVANI image generation request."});
    }
  });
}
