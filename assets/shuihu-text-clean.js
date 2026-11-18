/* 仅去除维基文库页面末尾的版权模板与机器标记，不删除小说结尾和评点。 */
(function(root){
 "use strict";
 function isSourceFooter(text){
   const s=String(text||"").replace(/[\u200b\ufeff\u00a0]/g," ").trim().replace(/\s+/g," ");
   if(!s)return true;
   if(/^(?:此(?:明朝|清朝|古代)?(?:作品|著作)|本作品)(?:在全世界)?(?:都)?属于公有领域[，,：:\s]|^此(?:明朝|清朝|古代)?作品在全世界都属于公有领域/.test(s))return true;
   if(/^(?:Public\s*domain\s*)+(?:(?:false|true)\s*)*$/i.test(s))return true;
   if(/^(?:(?:false|true)\s*){2,}$/i.test(s))return true;
   if(/^(?:PD-old|PD-China|CC0|copyright status|版权状态)(?:\s+\w+)*$/i.test(s))return true;
   return false;
 }
 function cleanParagraphs(paragraphs){
   if(!Array.isArray(paragraphs))return [];
   const cleaned=paragraphs.slice();
   // 只处理文章尾部的来源模板，绝不删除文学正文或有意义的结尾诗。
   while(cleaned.length && isSourceFooter(cleaned[cleaned.length-1]))cleaned.pop();
   return cleaned;
 }
 root.SHUIHU_TEXT_CLEAN={cleanParagraphs,isSourceFooter};
})(typeof window!=="undefined"?window:globalThis);
