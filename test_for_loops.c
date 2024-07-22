int main() 
{ int i,j,k,l,m; for (i = 0; i < 5; i++){for(j = 0; j < 5; j++)
{
for(k=0;k<5;k++){for(l=0;l<5;l++){
for(m=0;m<5;m++){if(i==j){
i=0;}else{break;
} }}}}}


for (i=0;i<3;i++)
{ for(j=0;j<3;j++)
{ if(j%2==0){
for (k=0;k<2;k++){l=k;
while(l<2){m=l;do{m++;}
while(m<2);l++;}}}}}

for(i=0;i<2;i++)
{ for (j=0;j<2;j++)
{ if(i!=j){
for(k=0;k<2;k++)
{ for(l=0;l<2;l++)
{ for(m=0;m<2;m++)
{m=m+1;
}}}}}}

}