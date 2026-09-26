// Bounded, outer-layer grid path search. Native KiCad DRC remains authoritative.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <queue>
#include <vector>
extern "C" {
void raster(uint8_t* img,int n,const double* xy,const int* counts,int contours,double step) {
 int off=0; double miny=1e9,maxy=-1e9;
 for(int c=0;c<contours;c++)for(int j=0;j<counts[c];j++,off++){miny=std::min(miny,xy[2*off+1]);maxy=std::max(maxy,xy[2*off+1]);}
 int lo=std::max(0,(int)std::ceil(miny/step)), hi=std::min(n-1,(int)std::floor(maxy/step));
 for(int y=lo;y<=hi;y++) {std::vector<double> xs;off=0;double yy=y*step;
  for(int c=0;c<contours;c++){int num=counts[c];for(int j=0;j<num;j++){int k=(j+1)%num;double ax=xy[2*(off+j)],ay=xy[2*(off+j)+1],bx=xy[2*(off+k)],by=xy[2*(off+k)+1];if((ay>yy)!=(by>yy))xs.push_back(ax+(yy-ay)*(bx-ax)/(by-ay));}off+=num;}
  std::sort(xs.begin(),xs.end());for(size_t k=0;k+1<xs.size();k+=2){int a=std::max(0,(int)std::ceil(xs[k]/step)),b=std::min(n-1,(int)std::floor(xs[k+1]/step));for(int x=a;x<=b;x++)img[y*n+x]=1;}
 }
}
int route(const uint8_t* blocked,const uint8_t* via,const uint8_t* starts,const uint8_t* goals,int n,int maxiter,int viacost,int* result,int maxout) {
 int nn=n*n,N=nn*2,gx0=n,gy0=n,gx1=0,gy1=0;
 for(int i=0;i<N;i++)if(goals[i]){int x=i%n,y=(i%nn)/n;gx0=std::min(gx0,x);gx1=std::max(gx1,x);gy0=std::min(gy0,y);gy1=std::max(gy1,y);}
 if(gx0==n)return -1;
 auto h=[&](int i){int x=i%n,y=(i%nn)/n,dx=std::max({gx0-x,0,x-gx1}),dy=std::max({gy0-y,0,y-gy1});return 100*std::max(dx,dy)+41*std::min(dx,dy);};
 struct Q{int f,g,i;bool operator<(const Q&o)const{return f>o.f;}};std::priority_queue<Q> q;
 std::vector<int> dist(N,2147483647),prev(N,-2);
 for(int i=0;i<N;i++)if(starts[i]&&!blocked[i]){dist[i]=0;prev[i]=-1;q.push({h(i),0,i});}
 const int dx[8]={1,-1,0,0,1,1,-1,-1},dy[8]={0,0,1,-1,1,-1,1,-1};int count=0;
 while(!q.empty()&&count++<maxiter){Q a=q.top();q.pop();if(a.g!=dist[a.i])continue;
  if(goals[a.i]){int j=a.i,k=0;while(j>=0){if(k>=maxout)return -3;result[k++]=j;j=prev[j];}return k;}
  int x=a.i%n,y=(a.i%nn)/n;
  for(int k=0;k<9;k++){int j,w;
   if(k==8){if(via[a.i%nn])continue;j=(a.i+nn)%N;w=viacost;}
   else {int xx=x+dx[k],yy=y+dy[k];if(xx<0||xx>=n||yy<0||yy>=n)continue;j=a.i+dx[k]+n*dy[k];w=k<4?100:141;if(k>=4&&(blocked[a.i+dx[k]]||blocked[a.i+n*dy[k]]))continue;}
   if(blocked[j])continue;
   if(prev[a.i]>=0 && j-a.i!=a.i-prev[a.i])w+=8;
   int cost=a.g+w;if(cost>=dist[j])continue;dist[j]=cost;prev[j]=a.i;q.push({cost+(int)(h(j)*1.015),cost,j});
  }
 }
 result[0]=count;
 return count>=maxiter?-4:-2;
}
}
extern "C" void flood(const uint8_t* blocked,const uint8_t* via,const uint8_t* starts,uint8_t* visited,int n) {
 int nn=n*n,N=nn*2;std::vector<int> q;q.reserve(N);
 for(int i=0;i<N;i++)if(starts[i]&&!blocked[i]){visited[i]=1;q.push_back(i);}
 for(size_t k=0;k<q.size();k++){int a=q[k],x=a%n,y=(a%nn)/n;
  int nb[5]={x<n-1?a+1:-1,x>0?a-1:-1,y<n-1?a+n:-1,y>0?a-n:-1,!via[a%nn]?(a+nn)%N:-1};
  for(int j:nb)if(j>=0&&!blocked[j]&&!visited[j]){visited[j]=1;q.push_back(j);}
 }
}
